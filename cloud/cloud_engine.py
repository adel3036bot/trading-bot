# ==================================================
# CLOUD ENGINE
# ==================================================

from datetime import datetime


class CloudEngine:

    def __init__(self):

        self.cloud_status = False

    # ==========================================
    # CONNECT CLOUD
    # ==========================================

    def connect(self):

        self.cloud_status = True

        print(
            "☁️ CLOUD ENGINE CONNECTED"
        )

        return True

    # ==========================================
    # STATUS
    # ==========================================

    def get_status(self):

        if self.cloud_status:

            return "ONLINE"

        return "OFFLINE"


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    cloud = CloudEngine()

    cloud.connect()

    print(

        "STATUS:",

        cloud.get_status()

    )


    