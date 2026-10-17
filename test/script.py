text = (
    "Successfully created file: C:\\Users\\Rashm\\Desktop\\sri_lanka_cricket_team.md\n"
)

parts = text.split(":")[-2] +":" + text.split(":")[-1]

print(parts)
