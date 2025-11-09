from app.utils import *
from flask import Flask, jsonify
from flask_restful import Api, Resource, reqparse
from flask_pymongo import PyMongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


class RegisterStudent(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("surname", type=str, required=True, help="Surname is required")
        self.parser.add_argument("first_name", type=str, required=True, help="First name is required")
        self.parser.add_argument("other_names", type=str, required=False)  # Optional
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("department", type=str, required=True, help="Department is required")
        self.parser.add_argument("faculty", type=str, required=True, help="Faculty is required")
        self.parser.add_argument("phone_number", type=str, required=True, help="Phone number is required")
        self.parser.add_argument("gender", type=str, required=True, help="Gender is required")
        self.parser.add_argument("role", type=str, required=True, help="Role is required (DOI or Student)")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")

    def post(self):
        args = self.parser.parse_args()

        surname = args["surname"].strip().title()
        first_name = args["first_name"].strip().title()
        other_names = args["other_names"].strip().title() if args["other_names"] else ""
        reg_no = args["reg_no"].strip().upper()
        department = args["department"].strip().title()
        faculty = args["faculty"].strip().title()
        phone_number = args["phone_number"].strip()
        gender = args["gender"].strip().lower()
        role = args["role"].strip().lower()
        password = args["password"].strip()

        # ---------- Validate gender ----------
        if gender not in ["male", "female"]:
            return jsonify({
                "status": "error",
                "message": "Gender must be either 'male' or 'female'"
            })

        # ---------- Validate role ----------
        if role not in ["doi", "student"]:
            return jsonify({
                "status": "error",
                "message": "Role must be either 'DOI' or 'Student'"
            })

        # ---------- Validate password ----------
        if len(password) < 6:
            return jsonify({
                "status": "error",
                "message": "Password must be at least 6 characters long"
            })

        # ---------- Check for existing record ----------
        existing_student = students.find_one({
            "$or": [
                {"reg_no": reg_no},
                {"phone_number": phone_number}
            ]
        })

        if existing_student:
            return jsonify({
                "status": "error",
                "message": "Student with this registration number or phone number already exists"
            })

        # ---------- Hash the password ----------
        hashed_password = generate_password_hash(password)

        # ---------- Insert into MongoDB ----------
        new_student = {
            "surname": surname,
            "first_name": first_name,
            "other_names": other_names,
            "reg_no": reg_no,
            "department": department,
            "faculty": faculty,
            "phone_number": phone_number,
            "gender": gender,
            "role": role,
            "password": hashed_password
        }

        result = students.insert_one(new_student)

        return jsonify({
            "status": "success",
            "message": "Student registered successfully",
            "data": {
                "id": str(result.inserted_id),
                "surname": surname,
                "first_name": first_name,
                "other_names": other_names,
                "reg_no": reg_no,
                "department": department,
                "faculty": faculty,
                "phone_number": phone_number,
                "gender": gender,
                "role": role
            }
        })


# ---------- ADD RESOURCE ----------
api.add_resource(RegisterStudent, "/api/v1/sifms/register/student")



# ---------- Login ----------
class StudentLogin(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()
        password = args["password"].strip()

        # ---------- Check if student exists ----------
        student = students.find_one({"reg_no": reg_no})

        if not student:
            return jsonify({
                "status": "error",
                "message": "Invalid registration number or password"
            })

        # ---------- Verify password ----------
        if not check_password_hash(student["password"], password):
            return jsonify({
                "status": "error",
                "message": "Invalid registration number or password"
            })

        # ---------- Build full name ----------
        full_name = f"{student['surname']} {student['first_name']} {student.get('other_names', '')}".strip()

        # ---------- Success ----------
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "data": {
                "full_name": full_name,
                "reg_no": student["reg_no"],
                "surname": student["surname"],
                "first_name": student["first_name"],
                "other_names": student.get("other_names", ""),
                "department": student["department"],
                "faculty": student["faculty"],
                "phone_number": student["phone_number"],
                "gender": student["gender"],
                "role": student["role"]
            }
        })


# ---------- ADD RESOURCE ----------
api.add_resource(StudentLogin, "/api/v1/sifms/login")



# ---------- STUDENT COMPLAINT ----------
class StudentComplaint(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")
        self.parser.add_argument("complaint", type=str, required=True, help="Complaint text is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()
        complaint_text = args["complaint"].strip()

        # ---------- Check if student exists ----------
        student = students.find_one({"reg_no": reg_no})

        if not student:
            return jsonify({
                "status": "error",
                "message": "No student found with the provided registration number"
            })

        # ---------- Prevent duplicate complaint ----------
        existing_complaint = complaints.find_one({
            "student_reg_no": reg_no,
            "complaint": complaint_text
        })

        if existing_complaint:
            return jsonify({
                "status": "error",
                "message": "You have already submitted this exact complaint"
            })

        # ---------- Prepare complaint data ----------
        complaint_data = {
            "student_reg_no": student["reg_no"],  
            "student_id": str(student["_id"]),
            "surname": student["surname"],
            "first_name": student["first_name"],
            "other_names": student.get("other_names", ""),
            "department": student["department"],
            "faculty": student["faculty"],
            "phone_number": student["phone_number"],
            "gender": student["gender"],
            "role": student["role"],
            "complaint": complaint_text,
            "timestamp": datetime.utcnow(),
            "responses": []
        }

        # ---------- Insert into complaints collection ----------
        result = complaints.insert_one(complaint_data)

        return jsonify({
            "status": "success",
            "message": "Complaint submitted successfully",
            "data": {
                "complaint_id": str(result.inserted_id),
                "reg_no": reg_no,
                "complaint": complaint_text
            }
        })


# ---------- ADD RESOURCE ----------
api.add_resource(StudentComplaint, "/api/v1/sifms/complaint")



# ---------- RESPOND TO COMPLAINT ----------
class RespondToComplaint(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("doi_reg_no", type=str, required=True, help="DOI registration number is required")
        self.parser.add_argument("student_reg_no", type=str, required=True, help="Student registration number is required")
        self.parser.add_argument("response_message", type=str, required=True, help="Response message is required")

    def post(self):
        args = self.parser.parse_args()
        doi_reg_no = args["doi_reg_no"].strip().upper()
        student_reg_no = args["student_reg_no"].strip().upper()
        response_message = args["response_message"].strip()

        # ---------- Check if DOI exists ----------
        doi = students.find_one({"reg_no": doi_reg_no})
        if not doi:
            return jsonify({
                "status": "error",
                "message": "DOI not found"
            })

        if doi["role"].lower() != "doi":
            return jsonify({
                "status": "error",
                "message": "Only DOI can respond to complaints"
            })

        # ---------- Check if student exists ----------
        student = students.find_one({"reg_no": student_reg_no})
        if not student:
            return jsonify({
                "status": "error",
                "message": "Student not found"
            })

        # ---------- Find the student's complaint ----------
        complaint = complaints.find_one({"student_reg_no": student_reg_no})
        if not complaint:
            return jsonify({
                "status": "error",
                "message": "No complaint found for this student"
            })

        # ---------- Create the response object ----------
        response_data = {
            "doi_reg_no": doi_reg_no,
            "doi_name": f"{doi.get('surname', '')} {doi.get('first_name', '')}".strip(),
            "response_message": response_message,
            "response_time": datetime.utcnow()
        }

        # ---------- Append the response ----------
        complaints.update_one(
            {"_id": ObjectId(complaint["_id"])},
            {"$push": {"responses": response_data}}
        )

        return jsonify({
            "status": "success",
            "message": "Response added successfully",
            "data": response_data
        })


# ---------- ADD RESOURCE ----------
api.add_resource(RespondToComplaint, "/api/v1/sifms/respond/complaint")


class GetStudentComplaints(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "reg_no",
            type=str,
            required=True,
            location="args",  # ✅ FIXED
            help="Registration number is required"
        )

    def get(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()

        # ---------- Check if student exists ----------
        student = students.find_one({"reg_no": reg_no})
        if not student:
            return jsonify({
                "status": "error",
                "message": "No student found with the provided registration number"
            })

        # ---------- Fetch all complaints by this student ----------
        student_complaints = list(complaints.find({"student_reg_no": reg_no}))

        if not student_complaints:
            return jsonify({
                "status": "success",
                "message": "No complaints found for this student",
                "data": []
            })

        # ---------- Format response ----------
        formatted_complaints = []
        for comp in student_complaints:
            formatted_complaints.append({
                "complaint_id": str(comp["_id"]),
                "complaint": comp["complaint"],
                "timestamp": comp["timestamp"],
                "responses": comp.get("responses", [])
            })

        return jsonify({
            "status": "success",
            "message": "Complaints retrieved successfully",
            "total_complaints": len(formatted_complaints),
            "data": formatted_complaints
        })


# ---------- ADD RESOURCE ----------
api.add_resource(GetStudentComplaints, "/api/v1/sifms/student/complaints")



class GetAllComplaints(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("reg_no", type=str, required=True, help="Registration number is required")

    def post(self):
        args = self.parser.parse_args()
        reg_no = args["reg_no"].strip().upper()

        # ---------- Check if student exists ----------
        student = students.find_one({"reg_no": reg_no})
        if not student:
            return jsonify({
                "status": "error",
                "message": "No user found with the provided registration number"
            })

        # ---------- Verify if the student is a DOI ----------
        if student.get("role", "").lower() != "doi":
            return jsonify({
                "status": "error",
                "message": "Access denied. Only DOI can view all complaints."
            })

        # ---------- Fetch all complaints ----------
        all_complaints = list(complaints.find())

        if not all_complaints:
            return jsonify({
                "status": "success",
                "message": "No complaints found in the system",
                "data": []
            })

        # ---------- Format the response ----------
        formatted_complaints = []
        for comp in all_complaints:
            formatted_complaints.append({
                "complaint_id": str(comp["_id"]),
                "student_reg_no": comp.get("student_reg_no"),
                "student_name": f"{comp.get('surname', '')} {comp.get('first_name', '')}".strip(),
                "complaint": comp.get("complaint"),
                "timestamp": comp.get("timestamp"),
                "responses": comp.get("responses", [])
            })

        return jsonify({
            "status": "success",
            "message": "All complaints retrieved successfully",
            "total_complaints": len(formatted_complaints),
            "data": formatted_complaints
        })


# ---------- ADD RESOURCE ----------
api.add_resource(GetAllComplaints, "/api/v1/sifms/all/complaints")
