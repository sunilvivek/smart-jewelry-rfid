# 💎 Smart RFID Jewelry Inventory System

A modern RFID-based Jewelry Inventory Management System developed using Flask, SQLite, Python, HTML, CSS, and Bootstrap.

This system helps jewelry stores efficiently manage ornaments, track inventory using RFID tags, generate QR codes automatically, search products instantly, and monitor stock availability in real time.

---

## 📌 Project Overview

Jewelry businesses often struggle with manual inventory tracking, misplaced ornaments, stock inconsistencies, and inefficient record management.

The Smart RFID Jewelry Inventory System addresses these challenges by providing a centralized platform for managing jewelry inventory with RFID identification and QR code generation.

Each ornament is assigned a unique RFID ID, allowing quick identification and tracking throughout its lifecycle.

---

## 🚀 Features

### Dashboard

* View total inventory count
* Monitor total inventory weight
* Track total inventory value
* View available stock count
* Clean and responsive dashboard interface

### Jewelry Management

* Add new jewelry items
* Store RFID ID, ornament details, purity, weight, and price
* Prevent duplicate RFID entries
* Edit existing jewelry records
* Delete jewelry records

### RFID Tracking

* Search inventory using RFID ID
* Retrieve ornament information instantly
* Simulates real RFID scanning workflow

### QR Code Generation

* Automatically generates QR codes when jewelry is added
* Stores QR codes in the system
* Displays QR codes in inventory records
* Supports QR tag printing

### Inventory Monitoring

* Mark items as Sold
* Track Available and Sold status
* Real-time inventory updates

### Search Functionality

* Search ornaments by RFID ID
* Fast inventory lookup

### QR Printing

* Generate printable QR labels
* Attach labels directly to ornaments
* Simplifies inventory identification

---

## 🖥️ System Workflow

Add Jewelry
↓
Assign RFID ID
↓
Generate QR Code
↓
Store in Database
↓
Search / Scan RFID
↓
View Product Details
↓
Mark as Sold
↓
Inventory Updates Automatically

---

## 🛠️ Technology Stack

### Backend

* Python
* Flask
* SQLAlchemy
* SQLite

### Frontend

* HTML5
* CSS3
* Bootstrap 5

### Additional Libraries

* qrcode
* Pillow

---

## 📂 Project Structure

```text
smart-jewelry-rfid/
│
├── app.py
├── requirements.txt
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── qrcodes/
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── add_jewelry.html
│   ├── inventory.html
│   ├── scan.html
│   ├── edit.html
│   └── print_qr.html
│
└── instance/
    └── jewelry.db
```

## ⚙️ Installation Guide

### Clone Repository

```bash
git clone https://github.com/sunilvivek/smart-jewelry-rfid.git
```

### Navigate to Project

```bash
cd smart-jewelry-rfid
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### macOS/Linux

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

---

## 📊 Database Fields

| Field         | Description            |
| ------------- | ---------------------- |
| id            | Primary Key            |
| rfid_id       | Unique RFID Identifier |
| ornament_name | Ornament Name          |
| weight        | Ornament Weight        |
| purity        | Gold/Silver Purity     |
| price         | Ornament Price         |
| status        | Available / Sold       |

---

## 🔐 Future Enhancements

* Real RFID Reader Integration (RC522)
* Barcode Support
* PDF Invoice Generation
* Sales Management Module
* Customer Management
* User Authentication
* Admin Dashboard
* Inventory Analytics
* Cloud Database Integration
* Multi-Store Inventory Support

---

## 🎯 Learning Outcomes

This project helped in understanding:

* Flask Web Development
* CRUD Operations
* Database Management using SQLite
* RFID-based Inventory Concepts
* QR Code Generation
* Responsive UI Design
* Python Backend Development
* Full Stack Application Development

---

## 👨‍💻 Author

**Sunil Vivek**

B.Tech Computer Science Engineering (Cybersecurity)

SRM Institute of Science and Technology

GitHub: https://github.com/sunilvivek

---

## 📜 License

This project is developed for educational and academic purposes.
