# type: ignore

"""Python script to build Swimming Canada Time Validation executable"""

import os
import shutil
import subprocess

import PyInstaller.__main__
import PyInstaller.utils.win32.versioninfo as vinfo

import semver  # type: ignore
import app_version
from dotenv import load_dotenv

print("Starting build process...\n")

load_dotenv(override=True)
ADMIN_MODE = os.getenv("ADMIN_MODE", "False")
PRIVATE_KEY_FILE = os.getenv("PRIVATE_KEY_FILE", "private.pem")
PUBLIC_KEY_FILE = os.getenv("PUBLIC_KEY_FILE", "public.pem")
SWIMRANKINGS_API_USER = os.getenv("SWIMRANKINGS_API_USER", "swimrankings")
SWIMRANKINGS_API_PASSWORD = os.getenv("SWIMRANKINGS_API_PASSWORD", "swimrankings")
HYTEK_DB_PASSWORD = os.getenv("HYTEK_DB_PASSWORD", "hytek")

# Remove any previous build artifacts
try:
    shutil.rmtree("build")
except FileNotFoundError:
    pass

# Remove any previous build artifacts
try:
    shutil.rmtree("dist")
except FileNotFoundError:
    pass


# Determine current git tag
git_ref = subprocess.check_output('git describe --tags --match "v*" --long', shell=True).decode("utf-8").rstrip()

APP_VERSION = app_version.git_semver(git_ref)

print(f"Building application, version: {APP_VERSION}")
version = semver.version.Version.parse(APP_VERSION)

with open("version.py", "w") as f:
    f.write('"""Version information"""\n\n')
    f.write(f'APP_VERSION = "{APP_VERSION}"\n')

    # Admin Mode
    f.write(f'ADMIN_MODE = {ADMIN_MODE}\n')
    f.write(f'PRIVATE_KEY_FILE = "{PRIVATE_KEY_FILE}"\n')
    f.write(f'PUBLIC_KEY_FILE = "{PUBLIC_KEY_FILE}"\n')
    f.write(f'SWIMRANKINGS_API_USER = "{SWIMRANKINGS_API_USER}"\n')
    f.write(f'SWIMRANKINGS_API_PASSWORD = "{SWIMRANKINGS_API_PASSWORD}"\n')
    f.write(f'HYTEK_DB_PASSWORD = "{HYTEK_DB_PASSWORD}"\n')
    f.write("SENTRY_DSN = None\n")

    f.flush()
    f.close()

# Create file info to embed in executable
v = vinfo.VSVersionInfo(
    ffi=vinfo.FixedFileInfo(
        filevers=(version.major, version.minor, version.patch, 0),
        prodvers=(version.major, version.minor, version.patch, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
    ),
    kids=[
        vinfo.StringFileInfo(
            [
                vinfo.StringTable(
                    "040904e4",
                    [
                        # https://docs.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource
                        # Required fields:
                        vinfo.StringStruct("CompanyName", "Swimm Ontario"),
                        vinfo.StringStruct("FileDescription", "Hytek Time Validation"),
                        vinfo.StringStruct("FileVersion", APP_VERSION),
                        vinfo.StringStruct("InternalName", "hytek_time_validate"),
                        vinfo.StringStruct("ProductName", "Hytek-Validate"),
                        vinfo.StringStruct("ProductVersion", APP_VERSION),
                        vinfo.StringStruct("OriginalFilename", "Hytek-Validate.exe"),
                        # Optional fields
                        vinfo.StringStruct("LegalCopyright", "(c) NGN Management Inc."),
                    ],
                )
            ]
        ),
        vinfo.VarFileInfo(
            [
                # 1033 -> Engligh; 1252 -> charsetID
                vinfo.VarStruct("Translation", [1033, 1252])
            ]
        ),
    ],
)
with open("Hytek-Validate.fileinfo", "w") as f:
    f.write(str(v))
    f.flush()
    f.close()

print("Invoking PyInstaller to generate executable...\n")

# Build it
PyInstaller.__main__.run(["--distpath=dist", "--workpath=build", "Hytek-Validate.spec"])

# Put back the original version.py

os.remove("version.py")

with open("version.py", "w") as f:
    f.write('"""Version information"""\n\n')
    f.write(f'APP_VERSION: str = "unreleased"\n')
    f.write("SENTRY_DSN: str | None = None\n")
    f.write(f'ADMIN_MODE: bool = {ADMIN_MODE}\n')
    f.write(f'PRIVATE_KEY_FILE: str = "{PRIVATE_KEY_FILE}"\n')
    f.write(f'PUBLIC_KEY_FILE: str = "{PUBLIC_KEY_FILE}"\n')
    f.write(f'SWIMRANKINGS_API_USER: str = "{SWIMRANKINGS_API_USER}"\n')
    f.write(f'SWIMRANKINGS_API_PASSWORD: str = "{SWIMRANKINGS_API_PASSWORD}"\n')
    f.write(f'HYTEK_DB_PASSWORD: str = "{HYTEK_DB_PASSWORD}"\n')

    f.flush()
    f.close()
