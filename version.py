import datetime

def generate_timestamp_version():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d.%H%M%S")

def write_version_to_file(version_string, filename="Version.txt"):
    with open(filename, 'w') as f:
        f.write(version_string)
    print(f"'{filename}' '{version_string}' 기록 완료.")

if __name__ == "__main__":
    version = generate_timestamp_version()
    write_version_to_file(version)