
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"

# PostgreSQL Docker container settings
CONTAINER_NAME = "weather_pipeline_db"
DATABASE_NAME = "weather_pipeline"
DB_USER = "postgres"


def run_command(command):
    """Run a command and stop if it fails."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def sha256_file(file_path):
    """Calculate SHA-256 hash of a local file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_file = BACKUP_DIR / f"weather_pipeline_{timestamp}.dump"
    checksum_file = backup_file.with_suffix(".sha256")
    container_backup = f"/tmp/weather_pipeline_{timestamp}.dump"

    success = False

    try:
        print("Starting PostgreSQL backup...")

        # 1. Create backup inside the Docker container
        run_command([
            "docker", "exec", CONTAINER_NAME,
            "pg_dump", "-U", DB_USER,
            "-d", DATABASE_NAME,
            "-Fc", "-f", container_backup
        ])

        # 2. Validate the archive
        archive_listing = run_command([
            "docker", "exec", CONTAINER_NAME,
            "pg_restore", "-l", container_backup
        ])

        if "weather_records" not in archive_listing:
            raise RuntimeError("Backup validation failed: expected table missing.")

        print("Archive validation passed.")

        # 3. Copy backup safely to Windows
        run_command([
            "docker", "cp",
            f"{CONTAINER_NAME}:{container_backup}",
            str(backup_file)
        ])

        # 4. Compare SHA-256 hashes
        local_hash = sha256_file(backup_file)

        container_hash_output = run_command([
            "docker", "exec", CONTAINER_NAME,
            "sha256sum", container_backup
        ])

        container_hash = container_hash_output.split()[0]

        if local_hash != container_hash:
            raise RuntimeError("SHA-256 verification failed!")

        # 5. Save checksum
        checksum_file.write_text(
            f"{local_hash}  {backup_file.name}\n",
            encoding="utf-8"
        )

        success = True

        print("\nBACKUP SUCCESSFUL")
        print(f"File: {backup_file.name}")
        print(f"Size: {backup_file.stat().st_size:,} bytes")
        print(f"SHA-256: {local_hash}")
        print("Archive validation: PASS")
        print("Checksum verification: PASS")

    except Exception as error:
        print(f"\nBACKUP FAILED: {error}", file=sys.stderr)

    finally:
        # Clean up temporary backup inside the container
        subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "rm", "-f", container_backup],
            capture_output=True,
            text=True
        )

        # Remove incomplete local files if backup failed
        if not success:
            for file_path in (backup_file, checksum_file):
                if file_path.exists():
                    file_path.unlink()
            print("Incomplete local backup files cleaned up.")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
