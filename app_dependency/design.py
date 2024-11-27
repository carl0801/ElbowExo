from PyQt5.QtGui import QColor

# Color for aaplication
RED = QColor("#F44336")
DARKER_RED = QColor("#D32F2F") 
GREEN = QColor("#4CAF50")
DARKER_GREEN = QColor("#388E3C")
YELLOW = QColor("#FFEB3B")
DARKER_YELLOW = QColor("#FBC02D")
BLUE = QColor("#007BFF")
DARKER_BLUE = QColor("#0056B3")

BACKGROUND_COLOR = QColor("#f4f4f4")

GREEN_BUTTON = """
                                    QPushButton {
                                        background-color: #4CAF50;  /* Original green background */
                                        border: none;
                                        color: white;
                                        padding: 10px 20px;
                                        text-align: center;
                                        text-decoration: none;
                                        font-size: 16px;
                                        font-weight: normal;
                                        border-radius: 8px;
                                    }
                                    QPushButton:hover {
                                        background-color: #45a049;  /* Original hover green */
                                    }
                                    QPushButton:pressed {
                                        background-color: #3e8e41;  /* Original pressed green */
                                    }"""
BLUE_BUTTON = """                                            QPushButton {
                                                background-color: #007BFF; /* Default Button Background */
                                                border: none;
                                                color: white;
                                                padding: 10px 20px;
                                                text-align: center;
                                                text-decoration: none;
                                                font-size: 16px;
                                                font-weight: normal;
                                                border-radius: 8px;
                                            }
                                            QPushButton:hover {
                                                background-color: #0069D9; /* Hover State */
                                            }
                                            QPushButton:pressed {
                                                background-color: #0056B3; /* Clicked State */
                                            }"""
RED_BUTTON = """
                                        QPushButton {
                                            background-color: #F44336;  /* Red background */
                                            border: none;
                                            color: white;
                                            padding: 10px 20px;
                                            text-align: center;
                                            text-decoration: none;
                                            font-size: 16px;
                                            font-weight: normal;
                                            border-radius: 8px;
                                        }
                                        QPushButton:hover {
                                            background-color: #E53935;  /* Darker red on hover */
                                        }
                                        QPushButton:pressed {
                                            background-color: #D32F2F;  /* Even darker red when pressed */
                                        }"""
