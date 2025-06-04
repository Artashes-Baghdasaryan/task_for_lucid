import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def create_database_and_tables():
    """Create database, user, and tables automatically."""
    
    # Common connection strings to try
    root_connections = [
        "mysql+pymysql://root:@localhost:3306",      # No password
        "mysql+pymysql://root:root@localhost:3306",   # Password: root
        "mysql+pymysql://root:password@localhost:3306", # Password: password
        "mysql+pymysql://root:mysql@localhost:3306",  # Password: mysql
        "mysql+pymysql://root:admin@localhost:3306",  # Password: admin
    ]
    
    print("Starting database setup...")
    print("=" * 50)
    
    working_connection = None
    
    # Try to connect with root to create database and user
    for connection_string in root_connections:
        print(f"🔍 Trying connection: {connection_string.split(':')[2].split('@')[0]}@localhost")
        
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                print("Root connection successful!")
                
                # Create database
                conn.execute(text("CREATE DATABASE IF NOT EXISTS social_posts_db"))
                print(" Database 'social_posts_db' created/verified")
                
                # Create user
                try:
                    conn.execute(text("CREATE USER IF NOT EXISTS 'social_user'@'localhost' IDENTIFIED BY 'userpassword123'"))
                    print(" User 'social_user' created/verified")
                except:
                    print("User 'social_user' already exists")
                
                # Grant privileges
                conn.execute(text("GRANT ALL PRIVILEGES ON social_posts_db.* TO 'social_user'@'localhost'"))
                conn.execute(text("FLUSH PRIVILEGES"))
                print("Privileges granted")
                
                conn.commit()
                working_connection = connection_string
                break
                
        except SQLAlchemyError as e:
            print(f"Failed: {str(e)[:100]}...")
        except Exception as e:
            print(f"Error: {str(e)[:100]}...")
    
    if not working_connection:
        print("\n Could not connect with root user. Please:")
        print("1. Make sure MySQL is running")
        print("2. Check your root password")
        print("3. Or run the SQL commands manually in MySQL Workbench")
        return False
    
    print("\n" + "=" * 50)
    print("📊 Creating tables...")
    
    # Now connect to the specific database to create tables
    db_connection = working_connection.replace("localhost:3306", "localhost:3306/social_posts_db")
    
    try:
        engine = create_engine(db_connection)
        with engine.connect() as conn:
            
            # Create users table
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
                
                INDEX idx_email (email),
                INDEX idx_active (is_active)
            )
            """
            conn.execute(text(users_table))
            print("Users table created")
            
            # Create posts table
            posts_table = """
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text TEXT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            )
            """
            conn.execute(text(posts_table))
            print("Posts table created")
            
            # Insert sample data
            sample_user = """
            INSERT IGNORE INTO users (email, hashed_password) VALUES 
            ('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/nVHcNkKmK')
            """
            conn.execute(text(sample_user))
            print("Sample user created (email: test@example.com, password: password123)")
            
            conn.commit()
            
            # Verify tables
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"Tables verified: {', '.join(tables)}")
            
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Database setup complete!")
    
    # Create .env file
    create_env_file()
    
    return True

def create_env_file():
    """Create .env file with database configuration."""
    
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    env_content = f"""# Database Configuration
DATABASE_URL=mysql+pymysql://social_user:userpassword123@localhost:3306/social_posts_db

# JWT Secret Key
SECRET_KEY={secret_key}

# Application Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAX_PAYLOAD_SIZE=1048576
CACHE_EXPIRE_MINUTES=5
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(".env file created with configuration")

def test_final_connection():
    """Test the final application connection."""
    
    print("\n" + "=" * 50)
    print("🧪 Testing final connection...")
    
    try:
        from sqlalchemy import create_engine
        
        # Test with the application connection string
        connection_string = "mysql+pymysql://social_user:userpassword123@localhost:3306/social_posts_db"
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as user_count FROM users"))
            count = result.fetchone()[0]
            print(f"✅ Connection successful! Found {count} users in database")
            
            result = conn.execute(text("SELECT COUNT(*) as post_count FROM posts"))
            count = result.fetchone()[0]
            print(f"✅ Found {count} posts in database")
            
        print("Your FastAPI application is ready to run!")
        return True
        
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("MySQL Database Setup Script")
    print("=" * 50)
    
    # Install required packages
    try:
        import sqlalchemy
        import pymysql
    except ImportError:
        print("Missing required packages. Please run:")
        print("pip install sqlalchemy pymysql")
        sys.exit(1)
    
    # Run setup
    success = create_database_and_tables()
    
    if success:
        test_final_connection()
        print("\n Next steps:")
        print("1. Run: python main.py")
        print("2. Open: http://localhost:8000")
        print("3. Test login with: test@example.com / password123")
    else:
        print("\n🔧 Manual setup required:")
        print("1. Open MySQL Workbench")
        print("2. Copy and paste the SQL commands from the first artifact")
        print("3. Run them in MySQL Workbench")
        print("4. Then run this script again")