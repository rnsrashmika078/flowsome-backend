path = r"C:\Users\Rashm\OneDrive\Desktop\Intern_call.txt"


fixed_path = path.replace("\\","\\\\")

with open(fixed_path, "r" , encoding="utf-8") as file:
    content = file.read()
    print(content)