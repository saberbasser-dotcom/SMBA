from flask import Flask, render_template, request, jsonify
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)
print("🔥 APP RUNNING 🔥")

# 🔹 إعداد الاتصال بقاعدة البيانات Supabase (PostgreSQL)
def get_connection():
    # أولاً: جرب DATABASE_URL من Railway (Supabase)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)

    # Fallback: استخدم الـ details الثابتة (للتطوير المحلي)
    return psycopg2.connect(
        host="db.texzdzbcaaatgorlkeupw.supabase.co",
        database="postgres",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        port="5432"
    )



# 🏠 الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/cash_receive')
def cash_receive():

    return render_template('cash_receive.html')

@app.route('/account_tree_json')
def account_tree_json():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Account_ID, Account_Name, TreeAccount_ID, IsParent FROM ACCOUNT_TREE")
    rows = cursor.fetchall()
    accounts = [
        {"id": r[0], "name": r[1], "parent": r[2], "IsParent": r[3]}
        for r in rows
    ]
    cursor.close()
    conn.close()
    return jsonify(accounts)

@app.route('/account_tree')
def account_tree():
    return render_template("account_tree.html")

# 📌 صفحة القبض النقدية
@app.route('/save_receipt', methods=['POST'])
def save_receipt():

    try:
        data = request.form

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(GeneralEntryNo) FROM CASH_HEAD")
        max_no = cursor.fetchone()[0]

        new_no = 1 if max_no is None else max_no + 1

        DepartmentEntryNo = int(data.get("DepartmentEntryNo") or 0)
        BranchID = data.get("BranchID")
        TranscationType = int(data.get("TranscationType") or 0)
        MovementType = int(data.get("MovementType") or 0)

        ReceiptNo = data.get("ReceiptNo")
        DepartmentID = data.get("DepartmentID")
        UserID = data.get("UserID")
        PrintCopies = int(data.get("PrintCopies") or 0)
        Status = int(data.get("Status") or 0)
        Credit_Acc = int(data.get("Credit_Acc") or 0)
        Amount = float(data.get("Amount") or 0)
        DATE = data.get("DATE")
        Notes = data.get("Notes")

        now_time = datetime.now()

        # ✅ تعديل: استخدم %s بدلاً من ? (PostgreSQL)
        insert_query = """
        INSERT INTO CASH_HEAD
        (GeneralEntryNo, DepartmentEntryNo, BranchEntryNo, TranscationType, MovementType,
        ReceiptNo, DepartmentID, BranchID, UserID, PrintCopies, Status, Credit_Acc,
        Amount, DATE, EditTime, LastEdit, Notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            new_no,
            DepartmentEntryNo,
            BranchID,
            TranscationType,
            MovementType,
            ReceiptNo,
            DepartmentID,
            BranchID,
            UserID,
            PrintCopies,
            Status,
            Credit_Acc,
            Amount,
            DATE,
            now_time,
            now_time,
            Notes
        ))

        details_amount = request.form.getlist("Amount1[]")
        details_note = request.form.getlist("ItemNote[]")
        details_debit = request.form.getlist("Debit[]")

        print(details_amount)
        print(details_note)
        print(details_debit)

        for i in range(len(details_amount)):

            # ✅ تعديل: استخدم %s بدلاً من ? (PostgreSQL)
            cursor.execute("""
                INSERT INTO CASH_DETAILS
                (GeneralEntryNo, Debit, Amount1, ItemNote)
                VALUES (%s, %s, %s, %s)
            """, (
                new_no,
                int(details_debit[i] or 0),
                float(details_amount[i] or 0),
                details_note[i]
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "تم الحفظ بنجاح",
            "id": new_no
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/add_account')
def add_account():
    return render_template('add_account.html')

@app.route('/save_account', methods=['POST'])
def save_account():
    try:
        parent_id = request.form.get('parentAccount')
        account_code = request.form.get('accountCode')
        account_name = request.form.get('accountName')

        active1 = 1
        level1 = request.form.get('level1', '1')
        is_parent = None
        type_val = 'account'

        if not parent_id or not account_code or not account_name:
            return jsonify({
                "success": False,
                "message": "البيانات المطلوبة ناقصة"
            })

        conn = get_connection()
        cursor = conn.cursor()

        # ✅ تعديل: استخدم %s بدلاً من ? (PostgreSQL)
        cursor.execute("SELECT COUNT(*) FROM ACC_TR WHERE Account_ID = %s", (account_code,))
        exists = cursor.fetchone()[0] > 0

        if exists:
            # ✅ تعديل: استخدم %s بدلاً من ? (PostgreSQL)
            cursor.execute("""
                UPDATE ACC_TR 
                SET TreeAccount_Name = %s, TreeAccount_ID = %s, Active1 = %s, Level1 = %s, IsParent = %s, type = %s
                WHERE Account_ID = %s
            """, (account_name, parent_id, active1, level1, is_parent, type_val, account_code))
        else:
            # ✅ تعديل: استخدم %s بدلاً من ? (PostgreSQL)
            cursor.execute("""
                INSERT INTO ACC_TR (Account_ID, TreeAccount_Name, TreeAccount_ID, Active1, Level1, IsParent, type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (account_code, account_name, parent_id, active1, level1, is_parent, type_val))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "تم إضافة الحساب بنجاح"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


# 🟢 تشغيل السيرفر (معدل للـ Railway)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
