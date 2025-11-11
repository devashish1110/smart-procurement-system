"""
COMPLETE DATA PIPELINE
Step 1: Extract from Excel (Atharva.xlsx)
Step 2: Clean and transform data
Step 3: Insert real data into PostgreSQL
Step 4: Generate synthetic data
Step 5: Insert synthetic data

Requirements:
pip install pandas openpyxl sqlalchemy psycopg2-binary faker numpy python-dateutil
"""
from sqlalchemy.dialects.postgresql import insert as pg_insert
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, MetaData
from faker import Faker
import random
import hashlib

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password properly
password_hash = pwd_context.hash("admin123")

# Initialize Faker for generating realistic fake data
fake = Faker('en_IN')  # Indian locale for realistic names/addresses
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ============================================
# STEP 1: DATABASE CONNECTION
# ============================================

class DatabaseManager:
    def __init__(self, db_url):
        """
        db_url format: postgresql://username:password@localhost:5432/database_name
        Example: postgresql://postgres:password@localhost:5432/procurement_db
        """
        self.engine = create_engine(db_url)
        print(f"✓ Connected to database")
    
    def execute_query(self, query):
        """Execute a query"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
            return result
    
    def insert_dataframe(self, df, table_name, if_exists='append'):
        """Insert pandas DataFrame into table"""
        df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
        print(f"✓ Inserted {len(df)} rows into {table_name}")
    
    def get_table_count(self, table_name):
        """Get row count of a table"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.fetchone()[0]

# ============================================
# STEP 2: EXTRACT REAL DATA FROM EXCEL
# ============================================

class ExcelDataExtractor:
    """
    Extracts data from your Atharva.xlsx file
    Assumes the file has sheets for different data types
    """
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        # Load all sheets
        self.excel_file = pd.ExcelFile(excel_path)
        print(f"✓ Loaded Excel file with sheets: {self.excel_file.sheet_names}")
    
    def extract_patient_visits(self):
        """Extract patient visit data from main sheet"""
        df = pd.read_excel(self.excel_path, sheet_name=0)
        df = df.dropna(subset=['Name', 'Unique id'], how='all')
        df = df.rename(columns={
            'Unique id': 'unique_id',
            'Name': 'name',
            'Gender': 'gender',
            'Date': 'visit_date',
            'M/E': 'time_slot',
            'Type of treatment': 'treatment_type',
            'Consultation': 'consultation_charge',
            'Medicine': 'medicine_charge',
            'Treatment': 'treatment_charge',
            'Total Bill Amount': 'total_amount',
            'Total amount received': 'amount_paid',
            'Balance': 'balance',
            'Cash Paid': 'cash_paid'
        })
        return df
    
    def extract_medicines(self):
        medicine_sheets = [s for s in self.excel_file.sheet_names if 'medicine' in s.lower() or 'drug' in s.lower()]
        if medicine_sheets:
            df = pd.read_excel(self.excel_path, sheet_name=medicine_sheets[0])
        else:
            df = pd.DataFrame()
        return df
    
    def extract_expenses(self):
        try:
            df = pd.read_excel(self.excel_path, sheet_name='Expenses')
        except:
            print("⚠ No expense sheet found")
            df = pd.DataFrame()
        return df

# ============================================
# STEP 3: DATA TRANSFORMATION & CLEANING
# ============================================

class DataTransformer:
    
    @staticmethod
    def clean_patient_data(df):
        patients = df[['unique_id', 'name', 'gender']].copy()
        patients = patients.drop_duplicates(subset=['unique_id'])
        
        # Fix missing or invalid gender
        patients['gender'] = patients['gender'].fillna('Other')
        patients['gender'] = patients['gender'].str.upper().str.strip()
        
        # Map to DB-valid values (PostgreSQL constraint: 'M' or 'F')
        def map_gender(x):
            if x in ['M', 'F']:
                return x
            else:
                return None  # Invalid gender → NULL in DB
        
        patients['gender'] = patients['gender'].apply(map_gender)
        
        # Optional: warn about invalid genders
        invalid_genders = patients[patients['gender'].isna()]
        if not invalid_genders.empty:
            print(f"⚠ Warning: {len(invalid_genders)} patient(s) had invalid gender values and were set to NULL")
        
        # Generate fake phone, email, address, DOB
        patients['phone'] = patients['unique_id'].apply(
            lambda x: f"+91{random.randint(7000000000, 9999999999)}"
        )
        patients['email'] = patients.apply(
            lambda row: f"{row['name'].lower().replace(' ', '.')}@email.com", 
            axis=1
        )
        patients['address'] = "Mumbai, India"
        patients['date_of_birth'] = datetime.now() - pd.to_timedelta(np.random.randint(6570, 29200, size=len(patients)), unit='D')
        patients['created_at'] = datetime.now()
        patients['name'] = patients['name'].str.strip()
        
        return patients

    @staticmethod
    def clean_visit_data(df, patient_id_map):
        visits = df.copy()
        visits['patient_id'] = visits['unique_id'].map(patient_id_map)
        visits['appointment_date'] = pd.to_datetime(visits['visit_date'], errors='coerce')
        visits['time_slot'] = visits['time_slot'].map({'M': 'M', 'E': 'E', 'Morning': 'M', 'Evening': 'E'})
        visits['treatment_id'] = 1
        visits['assigned_therapist'] = random.randint(1, 5)
        visits['assigned_doctor'] = random.randint(1, 3)
        visits['status'] = 'completed'
        visits['created_at'] = visits['appointment_date']
        return visits
    
    @staticmethod
    def clean_bill_data(df, appointment_ids):
        bills = df.copy()
        bills = bills.rename(columns={
            'Sr.no': 'Sr_no',
            'M/E': 'M_E',
            'Treatment Price as per Model': 'Treatment_Price_as_per_Model'
        })
        bills['bill_number'] = bills.apply(lambda row: f"BILL{row.name + 1:05d}", axis=1)
        if len(bills) <= len(appointment_ids):
            bills['appointment_id'] = appointment_ids[:len(bills)]
        else:
            bills = bills.iloc[:len(appointment_ids)]
            bills['appointment_id'] = appointment_ids
        for col in ['consultation_charge', 'medicine_charge', 'treatment_charge', 'total_amount', 'amount_paid', 'balance', 'cash_paid']:
            if col in bills.columns:
                bills[col] = pd.to_numeric(bills[col], errors='coerce').fillna(0)
        bills['payment_mode'] = bills.apply(lambda row: random.choice(['cash', 'card', 'upi', 'online']), axis=1)
        bills['is_online'] = bills['payment_mode'].isin(['card', 'upi', 'online'])
        bills['created_by'] = 1
        bills['created_at'] = datetime.now()
        return bills

# ============================================
# STEP 4: REAL DATA INSERTION WITH UPSERT
# ============================================

class RealDataInserter:
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def insert_users(self):
        users = pd.DataFrame([
            {'username': 'admin', 'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(), 'full_name': 'System Admin', 'role': 'admin', 'email': 'admin@clinic.com', 'phone': '+919876543210', 'is_active': True, 'created_at': datetime.now()},
            {'username': 'doctor_1', 'password_hash': hashlib.sha256('doctor123'.encode()).hexdigest(), 'full_name': 'Dr. Rajesh Sharma', 'role': 'doctor', 'email': 'doctor@clinic.com', 'phone': '+919876543211', 'is_active': True, 'created_at': datetime.now()},
            {'username': 'pharmacist_1', 'password_hash': hashlib.sha256('pharma123'.encode()).hexdigest(), 'full_name': 'Priya Patel', 'role': 'pharmacist', 'email': 'pharmacist@clinic.com', 'phone': '+919876543212', 'is_active': True, 'created_at': datetime.now()},
            {'username': 'receptionist_1', 'password_hash': hashlib.sha256('reception123'.encode()).hexdigest(), 'full_name': 'Amit Kumar', 'role': 'receptionist', 'email': 'reception@clinic.com', 'phone': '+919876543213', 'is_active': True, 'created_at': datetime.now()},
            {'username': 'therapist_1', 'password_hash': hashlib.sha256('therapy123'.encode()).hexdigest(), 'full_name': 'Sneha Reddy', 'role': 'therapist', 'email': 'therapist@clinic.com', 'phone': '+919876543214', 'is_active': True, 'created_at': datetime.now()}
        ])
        metadata = MetaData()
        metadata.reflect(bind=self.db.engine)
        users_table = metadata.tables['users']
        with self.db.engine.begin() as conn:
            for i in range(0, len(users), 50):
                chunk = users.iloc[i:i+50].to_dict(orient='records')
                stmt = pg_insert(users_table).values(chunk)
                stmt = stmt.on_conflict_do_nothing(index_elements=['username'])
                conn.execute(stmt)
        print(f"✓ Inserted (upsert) {len(users)} users into users table")
        return len(users)
    
    def insert_patients(self, patient_df):
        metadata = MetaData()
        metadata.reflect(bind=self.db.engine)
        patients_table = metadata.tables['patients']
        if 'patient_id' in patient_df.columns:
            patient_df = patient_df.drop('patient_id', axis=1)
        with self.db.engine.begin() as conn:
            for i in range(0, len(patient_df), 100):
                chunk = patient_df.iloc[i:i+100].to_dict(orient='records')
                stmt = pg_insert(patients_table).values(chunk)
                stmt = stmt.on_conflict_do_nothing(index_elements=['unique_id'])
                conn.execute(stmt)
        with self.db.engine.connect() as conn:
            result = conn.execute(text("SELECT patient_id, unique_id FROM patients"))
            patient_map = {row[1]: row[0] for row in result}
        return patient_map

# ============================================
# STEP 5: MAIN EXECUTION PIPELINE
# ============================================

def main():
    print("=" * 80)
    print("SMART PROCUREMENT SYSTEM - DATA PIPELINE")
    print("=" * 80)
    
    DB_URL = "postgresql://postgres:qK4Asnk0&8@localhost:5432/procurement"
    EXCEL_PATH = "C:/Users/DELL/Desktop/Atharva.xlsx"
    
    print("\n[STEP 1] Connecting to database...")
    db = DatabaseManager(DB_URL)
    
    print("\n[STEP 2] Extracting real data from Excel...")
    extractor = ExcelDataExtractor(EXCEL_PATH)
    patient_visits_df = extractor.extract_patient_visits()
    print(f"✓ Extracted {len(patient_visits_df)} patient visit records")
    
    print("\n[STEP 3] Transforming data...")
    transformer = DataTransformer()
    patients_df = transformer.clean_patient_data(patient_visits_df)
    print(f"✓ Cleaned {len(patients_df)} unique patients")
    
    print("\n[STEP 4] Inserting real data into database...")
    inserter = RealDataInserter(db)
    inserter.insert_users()
    patient_map = inserter.insert_patients(patients_df)
    
if __name__ == "__main__":
    main()
