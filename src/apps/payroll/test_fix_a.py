"""FIX-A numeric input and locked payroll regressions; synthetic data only."""
from datetime import date
from decimal import Decimal

from django.test import override_settings
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.payroll import tests as fixtures
from apps.payroll.models import EmployeeSalary, InsuranceRateConfig, Payroll, PersonalIncomeTaxBracket, TaxDeductionConfig
from apps.security.models import Role, User


@override_settings(AXES_ENABLED=False)
class PayrollInputSafetyTests(fixtures.PayrollTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        role, _ = Role.objects.get_or_create(role_code='FINANCE_OFFICER', defaults={'role_name': 'QA Finance'})
        cls.finance = User.objects.create_user(username='fix-a-finance', role=role)
        EmployeeSalary.objects.create(employee=cls.employee, current_basic_salary=1000000,
                                      effective_date=date(2020, 1, 1))

    def insurance_data(self, **changes):
        data = {'form_type': 'insurance', 'effective_from': '2025-01-01',
                'employee_social_insurance_rate': '0', 'employee_health_insurance_rate': '0',
                'employee_unemployment_insurance_rate': '0', 'employer_social_insurance_rate': '0',
                'employer_health_insurance_rate': '0', 'employer_unemployment_insurance_rate': '0'}
        return {**data, **changes}

    def test_finance_cannot_save_negative_insurance_or_lock_invalid_legacy_payroll(self):
        self.client.force_login(self.finance)
        response = self.client.post(reverse('portal:finance_tax_config'),
                                    self.insurance_data(employee_social_insurance_rate='-10'), follow=True)
        self.assertEqual(response.status_code, 200)
        # On the old implementation the invalid configuration is saved and used.
        invalid = InsuranceRateConfig.objects.filter(effective_from=date(2025, 1, 1)).first()
        if invalid:
            row = Payroll.objects.create(employee=self.employee, payroll_period=self.period,
                                         basic_salary=Decimal('1000000'))
            row.calculate()
            row.save()
            self.client.post(reverse('portal:finance_payroll_lock', args=[self.period.pk]))
            self.period.refresh_from_db()
            print('R2_01_BEFORE', self.period.status, row.insurance_amount, row.net_income, flush=True)
        self.assertIsNone(invalid, 'Finance must reject negative percentage before persisting it')
        self.insurance_cfg.refresh_from_db()
        self.assertIsNone(self.insurance_cfg.effective_to, 'Invalid POST must not close the old generation')

    def test_all_finance_numeric_config_inputs_reject_invalid_domains_without_closing_previous(self):
        self.client.force_login(self.finance)
        for name in InsuranceRateConfig.RATE_FIELDS:
            for invalid in ('-0.01', '100.01', 'NaN', 'Infinity', 'not-a-number'):
                with self.subTest(field=name, invalid=invalid):
                    self.client.post(reverse('portal:finance_tax_config'), self.insurance_data(**{name: invalid}))
                    self.assertFalse(InsuranceRateConfig.objects.filter(effective_from=date(2025, 1, 1)).exists())
        for name in ('self_deduction_monthly', 'dependent_deduction_monthly'):
            data = {'form_type': 'deduction', 'effective_from': '2025-01-01',
                    'self_deduction_monthly': '0', 'dependent_deduction_monthly': '0', name: '-1'}
            self.client.post(reverse('portal:finance_tax_config'), data)
            self.assertFalse(TaxDeductionConfig.objects.filter(effective_from=date(2025, 1, 1)).exists())
        for field, invalid in [('tax_rate', '101'), ('income_from_monthly', '-1'),
                               ('income_to_monthly', '0'), ('bracket_no', '0'), ('bracket_no', '1.5')]:
            data = {'form_type': 'bracket', 'effective_from': '2025-01-01',
                    'bracket_no': '1', 'income_from_monthly': '0', 'income_to_monthly': '', 'tax_rate': '0', field: invalid}
            self.client.post(reverse('portal:finance_tax_config'), data)
            self.assertFalse(PersonalIncomeTaxBracket.objects.filter(effective_from=date(2025, 1, 1)).exists())

    def test_configuration_clean_covers_admin_caps_rates_and_deductions(self):
        for field in InsuranceRateConfig.RATE_FIELDS + InsuranceRateConfig.MONEY_FIELDS:
            for value in (Decimal('-1'), Decimal('NaN')):
                with self.subTest(field=field, value=value):
                    config = InsuranceRateConfig(**{name: 0 for name in InsuranceRateConfig.RATE_FIELDS})
                    setattr(config, field, value)
                    with self.assertRaises(ValidationError):
                        config.clean()
        for field in ('self_deduction_monthly', 'dependent_deduction_monthly'):
            config = TaxDeductionConfig(self_deduction_monthly=0, dependent_deduction_monthly=0)
            setattr(config, field, '-1')
            with self.assertRaises(ValidationError):
                config.clean()

    def test_legacy_invalid_config_cannot_calculate_or_lock_and_identifies_employee(self):
        row = self.make_payroll(basic_salary=Decimal('1000000'))
        row.save()
        InsuranceRateConfig.objects.filter(pk=self.insurance_cfg.pk).update(employee_social_insurance_rate=-10)
        row.insurance_amount = Decimal('-100000')
        row.net_income = row.gross_income + 100000
        row.save()
        with self.assertRaises(ValidationError):
            row.calculate()
        self.client.force_login(self.finance)
        response = self.client.post(reverse('portal:finance_payroll_lock', args=[self.period.pk]), follow=True)
        self.period.refresh_from_db()
        self.assertEqual(self.period.status, 'Open')
        self.assertContains(response, self.employee.employee_code)

    def test_lock_checks_results_even_when_signature_is_current(self):
        row = self.make_payroll(basic_salary=Decimal('1000000'))
        for name, value in [('insurance_amount', -1), ('tax_amount', -1),
                            ('net_income', row.gross_income + 1), ('gross_income', Decimal('NaN'))]:
            with self.subTest(field=name):
                original = getattr(row, name)
                setattr(row, name, value)
                with self.assertRaises(ValidationError):
                    row.validate_calculated()
                setattr(row, name, original)

    def test_valid_boundaries_and_negative_net_policy_are_unchanged(self):
        self.client.force_login(self.finance)
        self.client.post(reverse('portal:finance_tax_config'), self.insurance_data(employee_social_insurance_rate='100'))
        cfg = InsuranceRateConfig.objects.get(effective_from=date(2025, 1, 1))
        self.assertEqual(cfg.employee_social_insurance_rate, Decimal('100'))
        row = self.make_payroll(basic_salary=Decimal('1000000'), deduction_amount=Decimal('1'))
        self.assertEqual(row.insurance_amount, Decimal('1000000'))
        self.assertEqual(row.net_income, Decimal('-1'))
        row.validate_calculated()

    def test_money_inputs_reject_nonfinite_and_wrong_types(self):
        for name in Payroll.INPUT_FIELDS:
            for value in ('NaN', 'Infinity', 'broken', -1):
                with self.subTest(field=name, value=value):
                    row = Payroll(payroll_period=self.period, employee=self.employee, basic_salary=1000000)
                    setattr(row, name, value)
                    with self.assertRaises(ValidationError):
                        row.calculate()
