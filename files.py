import os

# get current working directory

current_dir = os.getcwd()
print("current working directory: " , current_dir)

# get absolute path to file and directory
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
print(f"script path {script_path}" )
print(f"script dir {script_dir}" )

# define custom path
file_path = os.path.join(current_dir, "data" , "reports" , "summary.csv")
print("Safe Path:", file_path)


#checking existance of file or directory

check_file_path = os.path.join("data" , "notes.txt")

if os.path.exists(check_file_path):
    print("Path Exists!")
    
    if os.path.isdir(check_file_path):
        print("It is a valid file")
    if os.path.isfile(check_file_path):
        print("It is a directory!")
        
        
else:
    print("Path not exist!")
    
    
    
# breaking down path string

full_path = "/Users/username/project/data/notes.txt"

print("Directory" , os.path.dirname(full_path))
print("Filename" , os.path.basename(full_path))


filename, extension = os.path.splitext("notes.txt")
print("Name: " , filename, "| Extension: " , extension)

home_dir = os.path.expanduser("~");
print(f"HOME DIR {home_dir}")
