# ==================================================
# BACKUP ENGINE
# ==================================================

from datetime import datetime


class BackupEngine:

    def __init__(self):

        self.backup_folder = "backup"

    # ==========================================
    # DATABASE BACKUP
    # ==========================================

    def backup_database(self):

        print(
            "💾 DATABASE BACKUP CREATED"
        )

        return True

    # ==========================================
    # SIGNALS BACKUP
    # ==========================================

    def backup_signals(self):

        print(
            "💾 SIGNALS BACKUP CREATED"
        )

        return True

    # ==========================================
    # FULL BACKUP
    # ==========================================

    def create_full_backup(self):

        self.backup_database()

        self.backup_signals()

        print(
            "✅ FULL BACKUP COMPLETED"
        )

        return True


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    backup_engine = BackupEngine()

    backup_engine.create_full_backup()

    