import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sklearn.linear_model import LinearRegression
from fpdf import FPDF
import hashlib
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pyttsx3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================== CONSTANTS ========================
SUBJECTS = ["Machine Learning", "UHV", "DMGT", "DBMS", "OT", "ES"]
CSV_FILE = "student_data.csv"

# ======================== CORE FUNCTIONALITY ========================
class StudentAnalyzer:
    def __init__(self):
        self.initialize_database()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
    def initialize_database(self):
        """Initialize or validate the CSV database"""
        if not os.path.exists(CSV_FILE):
            df = pd.DataFrame(columns=["Name", "ID", "Password", "Email", "Phone"] + SUBJECTS)
            df.to_csv(CSV_FILE, index=False)
        else:
            try:
                df = pd.read_csv(CSV_FILE)
                required_cols = ["Name", "ID", "Password", "Email", "Phone"] + SUBJECTS
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = "" if col in ["Name", "ID", "Password", "Email", "Phone"] else 0
                df.to_csv(CSV_FILE, index=False)
            except:
                df = pd.DataFrame(columns=required_cols)
                df.to_csv(CSV_FILE, index=False)
    
    def hash_password(self, password):
        """Securely hash passwords"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_student(self):
        """Register new student with all details"""
        print("\n" + "="*40)
        print("STUDENT REGISTRATION PORTAL")
        print("="*40)
        
        name = input("Enter student full name: ")
        student_id = input("Create student ID: ")
        email = input("Enter student email: ")
        phone = input("Enter parent phone number: ")
        password = self.hash_password(input("Create password: "))
        
        marks = []
        for sub in SUBJECTS:
            while True:
                try:
                    mark = int(input(f"Enter {sub} marks (0-100): "))
                    if 0 <= mark <= 100:
                        marks.append(mark)
                        break
                    else:
                        print("Invalid marks! Enter between 0-100.")
                except ValueError:
                    print("Numbers only please!")
        
        # Calculate performance metrics
        percentage = round(sum(marks) / len(marks), 2)
        grade = self.assign_grade(percentage)
        
        # Create student record
        student_data = {
            "Name": name,
            "ID": student_id,
            "Password": password,
            "Email": email,
            "Phone": phone,
            "Percentage": percentage,
            "Grade": grade
        }
        student_data.update({sub: mark for sub, mark in zip(SUBJECTS, marks)})
        
        # Save to CSV
        df = pd.read_csv(CSV_FILE) if os.path.exists(CSV_FILE) else pd.DataFrame(columns=["Name", "ID", "Password", "Email", "Phone"] + SUBJECTS + ["Percentage", "Grade"])
        df = pd.concat([df, pd.DataFrame([student_data])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        
        print(f"\nSuccess! {name} registered with ID {student_id}")
        self.engine.say(f"Registration successful for {name}")
        self.engine.runAndWait()
        
    def assign_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B+'
        elif percentage >= 60: return 'B'
        elif percentage >= 50: return 'C'
        elif percentage >= 40: return 'D'
        else: return 'F'
    
    def login(self):
        """Student login system"""
        print("\n" + "="*40)
        print("STUDENT LOGIN PORTAL")
        print("="*40)
        
        student_id = input("Enter your student ID: ")
        password = self.hash_password(input("Enter your password: "))
        
        df = pd.read_csv(CSV_FILE)
        student = df[(df["ID"] == student_id) & (df["Password"] == password)]
        
        if not student.empty:
            print(f"\nWelcome {student['Name'].values[0]}!")
            return student.iloc[0]
        else:
            print("\nInvalid credentials! Please try again.")
            return None
    
    def generate_pdf_report(self, student_data):
        """Generate professional PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="OFFICIAL ACADEMIC REPORT", ln=1, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="AI-Powered Performance Analysis", ln=1, align='C')
        
        # Student Info
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Student Name: {student_data['Name']}", ln=1)
        pdf.cell(200, 10, txt=f"Student ID: {student_data['ID']}", ln=1)
        pdf.cell(200, 10, txt=f"Overall Percentage: {student_data['Percentage']}%", ln=1)
        pdf.cell(200, 10, txt=f"Grade: {student_data['Grade']}", ln=1)
        
        # Marks Table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Subject-wise Performance:", ln=1)
        pdf.set_font("Arial", size=10)
        
        col_width = 40
        row_height = 10
        for sub in SUBJECTS:
            pdf.cell(col_width, row_height, txt=sub, border=1)
            pdf.cell(col_width, row_height, txt=f"{student_data[sub]}%", border=1, ln=1)
        
        # Save PDF
        filename = f"Report_{student_data['ID']}.pdf"
        pdf.output(filename)
        print(f"\nPDF report generated: {filename}")
        return filename
    
    def send_email_report(self, student_data):
        """Send report via email (using SMTP)"""
        try:
            # Email configuration (replace with your SMTP details)
            sender_email = "your_email@gmail.com"
            sender_password = "your_password"
            receiver_email = student_data['Email']
            
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = f"Academic Report for {student_data['Name']}"
            
            body = f"""
            Dear Parent/Guardian,
            
            Please find attached the performance report for {student_data['Name']}.
            
            Overall Percentage: {student_data['Percentage']}%
            Grade: {student_data['Grade']}
            
            Regards,
            School Analytics Team
            """
            message.attach(MIMEText(body, "plain"))
            
            # Attach PDF
            pdf_path = self.generate_pdf_report(student_data)
            with open(pdf_path, "rb") as attachment:
                part = MIMEText(attachment.read(), "application/pdf")
                part.add_header("Content-Disposition", f"attachment; filename= {pdf_path}")
                message.attach(part)
            
            # Send email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            
            print(f"\nReport sent to {receiver_email}")
            return True
        except Exception as e:
            print(f"\nEmail failed: {str(e)}")
            return False
    
    def predict_future_performance(self, student_id):
        """AI prediction of future scores"""
        df = pd.read_csv(CSV_FILE)
        student_data = df[df["ID"] == student_id]
        
        if len(student_data) < 2:
            return "Insufficient data for predictions (need at least 2 records)"
        
        # Prepare data
        X = np.array(range(len(student_data))).reshape(-1, 1)
        y = student_data["Percentage"].values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next score
        next_score = model.predict([[len(student_data)]])[0]
        next_score = max(0, min(100, round(next_score, 2)))
        
        # Generate prediction statement
        trend = "improving" if next_score > y[-1] else "declining" if next_score < y[-1] else "stable"
        prediction = (
            f"AI Prediction for {student_data['Name'].values[0]}:\n"
            f"Current Percentage: {y[-1]}%\n"
            f"Next Test Prediction: {next_score}% ({trend} trend)\n"
            f"Confidence: {round(model.score(X, y)*100, 2)}%"
        )
        
        return prediction
    
    def visualize_performance(self, student_data):
        """Create animated performance graph"""
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.title(f"Performance Analysis for {student_data['Name']}")
        plt.xlabel("Subjects")
        plt.ylabel("Marks (%)")
        plt.ylim(0, 100)
        
        bars = plt.bar(SUBJECTS, [0]*len(SUBJECTS), color='skyblue')
        
        def animate(i):
            for bar, subject in zip(bars, SUBJECTS):
                bar.set_height(min(student_data[subject], (i+1)*10))
            return bars
        
        ani = FuncAnimation(fig, animate, frames=10, interval=200, blit=True)
        filename = f"Performance_{student_data['ID']}.gif"
        ani.save(filename, writer='pillow')
        print(f"\nAnimation saved as {filename}")
        return filename
    
    def class_statistics(self):
        """Generate comprehensive class report"""
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            return "No student data available"
        
        # Basic stats
        class_avg = round(df["Percentage"].mean(), 2)
        topper = df.loc[df["Percentage"].idxmax()]
        weak = df.loc[df["Percentage"].idxmin()]
        
        # Subject analysis
        sub_avg = df[SUBJECTS].mean().round(2)
        hardest_sub = sub_avg.idxmin()
        easiest_sub = sub_avg.idxmax()
        
        # Grade distribution
        grades = df["Grade"].value_counts().sort_index()
        
        # Create report
        report = (
            f"\n=== CLASS PERFORMANCE REPORT ===\n"
            f"Total Students: {len(df)}\n"
            f"Class Average: {class_avg}%\n"
            f"Topper: {topper['Name']} ({topper['Percentage']}%)\n"
            f"Needs Improvement: {weak['Name']} ({weak['Percentage']}%)\n\n"
            f"Subject Analysis:\n"
            f"Easiest Subject: {easiest_sub} ({sub_avg[easiest_sub]}% avg)\n"
            f"Hardest Subject: {hardest_sub} ({sub_avg[hardest_sub]}% avg)\n\n"
            f"Grade Distribution:\n{grades.to_string()}"
        )
        
        return report

# ======================== MAIN APPLICATION ========================
def main():
    analyzer = StudentAnalyzer()
    
    while True:
        print("\n" + "="*40)
        print("AI STUDENT PERFORMANCE ANALYZER")
        print("="*40)
        print("1. Register New Student")
        print("2. Student Login")
        print("3. Class Statistics")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            analyzer.register_student()
        elif choice == "2":
            student = analyzer.login()
            if student is not None:
                while True:
                    print("\n" + "="*30)
                    print(f"WELCOME {student['Name'].upper()}")
                    print("="*30)
                    print("1. View My Report")
                    print("2. Email Report to Parents")
                    print("3. Predict Future Performance")
                    print("4. View Performance Animation")
                    print("5. Logout")
                    
                    sub_choice = input("\nEnter choice (1-5): ")
                    
                    if sub_choice == "1":
                        analyzer.generate_pdf_report(student)
                    elif sub_choice == "2":
                        analyzer.send_email_report(student)
                    elif sub_choice == "3":
                        print("\n" + analyzer.predict_future_performance(student['ID']))
                    elif sub_choice == "4":
                        analyzer.visualize_performance(student)
                    elif sub_choice == "5":
                        break
                    else:
                        print("Invalid choice! Try again.")
        elif choice == "3":
            print(analyzer.class_statistics())
        elif choice == "4":
            print("\nThank you for using the Student Performance Analyzer!")
            break
        else:
            print("Invalid choice! Please enter 1-4.")

if __name__ == "__main__":
    main()