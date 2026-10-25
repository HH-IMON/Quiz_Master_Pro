from werkzeug.security import generate_password_hash
from database import execute_query, get_db_connection

def fix_admin_password():
    print("Fixing admin password...")
    
    # Generate new hash for 'admin123'
    password = 'admin123'
    new_hash = generate_password_hash(password)
    
    print(f"Generated new hash: {new_hash}")
    
    # Update database
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Update the admin user (assuming id=1 or username='admin')
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'admin'",
                (new_hash,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                print("Admin password successfully updated to 'admin123'")
            else:
                print("Admin user not found in database!")
                
        except Exception as e:
            print(f"Error updating password: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        print("❌ Could not connect to database")

if __name__ == "__main__":
    fix_admin_password()
