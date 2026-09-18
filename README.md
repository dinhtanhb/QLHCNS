# IHRMS

Internal Administration & Human Resource Management System

## Overview

IHRMS là hệ thống quản lý nội bộ doanh nghiệp bao gồm:

- Organization Management
- Human Resource Management
- Recruitment Management
- Attendance Management
- Leave Management
- Payroll Management
- Contract Management
- Document Management
- Task Management
- KPI Management
- Asset Management
- Procurement Management
- Dashboard & Reporting
- Microsoft 365 Integration

---

## Technology Stack

### Backend

- Python 3.12
- Django 5
- Django REST Framework

### Frontend

- Bootstrap 5
- AdminLTE 3
- JavaScript
- jQuery

### Database

- Microsoft SQL Server

### Authentication

- JWT
- Microsoft Entra ID

### Storage

- SharePoint
- OneDrive

---

## Environment

### Development

VS Code

### Test

SIT / UAT

### Production

Windows Server
IIS
SQL Server

---

## Project Structure

```text
ihrms/

config/

apps/

static/

media/

templates/

logs/
```

---

## Install

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate

```bash
venv\Scripts\activate
```

### Install Package

```bash
pip install -r requirements.txt
```

### Apply Migration

```bash
python manage.py migrate
```

### Create Admin User

```bash
python manage.py createsuperuser
```

### Run Development Server

```bash
python manage.py runserver
```

---

## Modules

### Phase 1

- Organization
- HRM

### Phase 2

- Recruitment
- Attendance
- Leave

### Phase 3

- Payroll
- Contracts

### Phase 4

- Documents
- Tasks
- KPI

### Phase 5

- Assets
- Procurement

### Phase 6

- Dashboard
- Microsoft 365 Integration

---

## Documentation

Refer to:

- 00_Project_Charter.md
- 01_BRD_MASTER.md
- 02_Solution_Architecture.md
- 03_Database_Design.md
- 99_Architecture_Baseline.md

---

## Status

Architecture Locked

Ready For Development