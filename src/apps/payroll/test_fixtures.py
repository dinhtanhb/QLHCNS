"""Synthetic statutory configuration for workflow tests only; never loaded into live databases."""
from datetime import date
from decimal import Decimal


def create_calculation_rates():
    from apps.payroll.models import InsuranceRateConfig, TaxDeductionConfig, PersonalIncomeTaxBracket
    InsuranceRateConfig.objects.create(effective_from=date(2020,1,1),
        employee_social_insurance_rate=8, employee_health_insurance_rate=Decimal('1.5'),
        employee_unemployment_insurance_rate=1, employer_social_insurance_rate=Decimal('17.5'),
        employer_health_insurance_rate=3, employer_unemployment_insurance_rate=1)
    TaxDeductionConfig.objects.create(effective_from=date(2020,1,1),
        self_deduction_monthly=11000000, dependent_deduction_monthly=4400000)
    PersonalIncomeTaxBracket.objects.create(effective_from=date(2020,1,1),bracket_no=1,
        income_from_monthly=0, tax_rate=5)
