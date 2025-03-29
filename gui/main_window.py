from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStatusBar, QMenuBar, QMenu, QMessageBox,
    QLabel, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QFileDialog, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QAction

# Import tab components
from gui.download_tab import DownloadTab
from gui.process_tab import ProcessTab
from gui.metadata_tab import MetadataTab
from gui.upload_tab import UploadTab

# Import database manager
from database.db_manager import DatabaseManager

import logging
import os
logger = logging.getLogger("TikTok2YouTube.MainWindow")

class SettingsDialog(QDialog):
    """Dialog for editing application settings"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # FFmpeg path
        self.ffmpeg_path = QLineEdit(self.config.get("ffmpeg_path", "ffmpeg"))
        
        # FFmpeg browse button
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.ffmpeg_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_ffmpeg)
        browse_layout.addWidget(browse_btn)
        form_layout.addRow("FFmpeg Path:", browse_layout)
        
        # Videos directory
        self.videos_dir = QLineEdit(self.config.get("videos_dir", "./videos"))
        videos_browse_btn = QPushButton("Browse...")
        videos_browse_btn.clicked.connect(self.browse_videos_dir)
        videos_layout = QHBoxLayout()
        videos_layout.addWidget(self.videos_dir)
        videos_layout.addWidget(videos_browse_btn)
        form_layout.addRow("Videos Directory:", videos_layout)
        
        # Output directory
        self.output_dir = QLineEdit(self.config.get("output_dir", "./output"))
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(output_browse_btn)
        form_layout.addRow("Output Directory:", output_layout)
        
        layout.addLayout(form_layout)
        
        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def browse_ffmpeg(self):
        """Browse for FFmpeg executable"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select FFmpeg Executable",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.ffmpeg_path.setText(file_path)
    
    def browse_videos_dir(self):
        """Browse for videos directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Videos Directory",
            self.videos_dir.text()
        )
        
        if dir_path:
            self.videos_dir.setText(dir_path)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir.text()
        )
        
        if dir_path:
            self.output_dir.setText(dir_path)
    
    def accept(self):
        """Save settings when dialog is accepted"""
        # Update config with new values
        self.config.set("ffmpeg_path", self.ffmpeg_path.text())
        self.config.set("videos_dir", self.videos_dir.text())
        self.config.set("output_dir", self.output_dir.text())
        
        # Let parent class handle dialog closure
        super().accept()

class MainWindow(QMainWindow):
    """
    Main application window that hosts the tab interface and 
    coordinates between different components of the application.
    
    This class serves as the central hub for the application, managing
    the UI components and facilitating communication between them.
    """
    
    def __init__(self, config):
        """
        Initialize the main window with proper layout and components.
        
        Args:
            config: Application configuration manager
        """
        super().__init__()
        
        # Store configuration reference
        self.config = config
        
        # Initialize database manager
        self.db = DatabaseManager()
        
        # Set up window properties
        self.setWindowTitle("TikTok to YouTube Shorts Automation")
        self.setMinimumSize(1000, 700)  # Set a reasonable minimum size
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.create_tabs()
        
        # Create status bar with additional information
        self.create_status_bar()
        
        # Create menu bar
        self.create_menu()
        
        # Connect signals between components
        self.connect_signals()
        
        # Start periodic status updates
        self.start_status_updates()
        
        logger.info("Main window initialized")
    
    def create_tabs(self):
        """
        Create and set up the tab widget with all necessary tabs.
        
        This initializes each tab component and adds them to the tab widget
        in the appropriate order for the workflow.
        """
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs with database access
        self.download_tab = DownloadTab(self.config)
        self.process_tab = ProcessTab(self.config)
        self.metadata_tab = MetadataTab(self.config)
        self.upload_tab = UploadTab(self.config)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.download_tab, "Download")
        self.tab_widget.addTab(self.process_tab, "Process")
        self.tab_widget.addTab(self.metadata_tab, "Metadata")
        self.tab_widget.addTab(self.upload_tab, "Upload")
        
        # Optional: add dashboard as first tab if implemented later
        # self.dashboard_tab = DashboardTab(self.config, self.db)
        # self.tab_widget.insertTab(0, self.dashboard_tab, "Dashboard")
        # self.tab_widget.setCurrentIndex(0)
    
    def create_status_bar(self):
        """
        Create an enhanced status bar with additional information.
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to the status bar
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)  # Stretch factor 1
        
        # Add video count label
        self.video_count_label = QLabel("Videos: 0")
        self.status_bar.addPermanentWidget(self.video_count_label)
        
        # Add processing status label
        self.processing_status_label = QLabel("Processing: None")
        self.status_bar.addPermanentWidget(self.processing_status_label)
    
    def create_menu(self):
        """
        Create the application menu bar with actions.
        
        Sets up the menus and actions for the application window.
        """
        # Create menu bar
        self.menu_bar = self.menuBar()
        
        # File menu
        file_menu = self.menu_bar.addMenu("&File")
        
        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        settings_action.setShortcut("Ctrl+,")
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Alt+F4")
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = self.menu_bar.addMenu("&Tools")
        
        # Refresh data action
        refresh_action = QAction("&Refresh Data", self)
        refresh_action.triggered.connect(self.refresh_data)
        refresh_action.setShortcut("F5")
        tools_menu.addAction(refresh_action)
        
        # Clear all data action (with confirmation)
        clear_action = QAction("&Clear All Data", self)
        clear_action.triggered.connect(self.confirm_clear_data)
        tools_menu.addAction(clear_action)
        
        # Help menu
        help_menu = self.menu_bar.addMenu("&Help")
        
        # Documentation action
        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """
        Connect signals between tabs for workflow coordination.
        
        This method sets up signal connections to allow the different tabs
        to communicate with each other and pass data through the workflow.
        """
        # Download completion -> Process tab
        self.download_tab.video_downloaded.connect(self.on_video_downloaded)
        
        # Processing completion -> Metadata tab
        self.process_tab.video_processed.connect(self.on_video_processed)
        
        # Metadata completion -> Upload tab
        self.metadata_tab.metadata_ready.connect(self.on_metadata_ready)
        
        # Connect tab changes to handle workflow navigation
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def on_video_downloaded(self, video_path, title):
        """
        Handle video downloaded signal.
        
        This method is called when a video is downloaded and adds it to the
        processing tab and the database.
        
        Args:
            video_path: Path to the downloaded video
            title: Video title
        """
        # Add to database
        try:
            video_id = self.db.add_video(video_path, title)
            logger.info(f"Added video to database: {os.path.basename(video_path)} (ID: {video_id})")
            
            # Update status
            self.status_label.setText(f"Downloaded: {os.path.basename(video_path)}")
            
            # Forward to process tab
            self.process_tab.add_video(video_path, title)
            
            # Update video count
            self.update_status_counts()
            
            # Switch to process tab if auto-navigation is enabled
            if self.config.get("auto_navigate", True):
                self.tab_widget.setCurrentIndex(1)  # Process tab
                
        except Exception as e:
            logger.error(f"Error adding video to database: {e}")
            QMessageBox.warning(self, "Database Error", 
                              f"Error adding video to database: {str(e)}")
    
    def on_video_processed(self, video_path, title):
        """
        Handle video processed signal.
        
        This method is called when a video is processed and adds it to the
        metadata tab.
        
        Args:
            video_path: Path to the processed video
            title: Video title
        """
        # Update database with processed info
        try:
            # Find the original video in the database
            videos = self.db.get_all_videos()
            original_video = None
            
            for video in videos:
                # Check if this processed video is related to an original
                if title == video["title"] or os.path.basename(video_path).startswith(os.path.basename(video["filepath"]).split('.')[0]):
                    original_video = video
                    break
            
            if original_video:
                # Update processing info
                self.db.add_processing_info(
                    original_video["id"], 
                    video_path,
                    self.config.get("processing", {})
                )
                
                # Update status
                self.status_label.setText(f"Processed: {os.path.basename(video_path)}")
            
            # Forward to metadata tab
            self.metadata_tab.add_video(video_path, title)
            
            # Update processing status
            self.update_status_counts()
            
            # Switch to metadata tab if auto-navigation is enabled
            if self.config.get("auto_navigate", True):
                self.tab_widget.setCurrentIndex(2)  # Metadata tab
                
        except Exception as e:
            logger.error(f"Error updating processing info: {e}")
    
    def on_metadata_ready(self, video_path, title):
        """
        Handle metadata ready signal.
        
        This method is called when metadata is ready and adds the video
        to the upload queue.
        
        Args:
            video_path: Path to the processed video
            title: Video title
        """
        # Forward to upload tab
        self.upload_tab.add_to_queue(video_path, title)
        
        # Update status
        self.status_label.setText(f"Metadata ready: {title}")
        
        # Switch to upload tab if auto-navigation is enabled
        if self.config.get("auto_navigate", True):
            self.tab_widget.setCurrentIndex(3)  # Upload tab
    
    def on_tab_changed(self, index):
        """
        Handle tab changes to update the UI for the selected tab.
        
        Args:
            index: Index of the newly selected tab
        """
        # Update status bar message based on selected tab
        tab_messages = [
            "Download TikTok videos for processing",
            "Apply video enhancements and effects",
            "Generate and optimize metadata for YouTube",
            "Schedule and manage YouTube uploads"
        ]
        
        if 0 <= index < len(tab_messages):
            self.status_label.setText(tab_messages[index])
    
    def start_status_updates(self):
        """Start periodic status bar updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status_counts)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        self.update_status_counts()
    
    def update_status_counts(self):
        """Update status bar with current counts"""
        try:
            # Get video counts
            all_videos = self.db.get_all_videos()
            processing_videos = [v for v in all_videos if v["status"] == "processing"]
            
            # Update labels
            self.video_count_label.setText(f"Videos: {len(all_videos)}")
            
            if processing_videos:
                self.processing_status_label.setText(f"Processing: {len(processing_videos)}")
            else:
                self.processing_status_label.setText("Processing: None")
                
        except Exception as e:
            logger.error(f"Error updating status counts: {e}")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config, self)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            # Refresh tabs with new settings
            self.refresh_data()
    
    def show_documentation(self):
        """Show documentation dialog"""
        QMessageBox.information(
            self,
            "Documentation",
            "The documentation for this application is available in the README.md file.\n\n"
            "You can also check the project website for more information."
        )
    
    def show_about(self):
        """Show about dialog with information about the application"""
        QMessageBox.about(
            self,
            "About TikTok to YouTube Shorts Automation",
            "This application automates the process of repurposing TikTok content to YouTube Shorts.\n\n"
            "Features:\n"
            "• TikTok content acquisition via Telegram bot\n"
            "• Advanced video processing with FFmpeg\n"
            "• Metadata generation and optimization\n"
            "• YouTube upload management and scheduling\n\n"
            "Version: 1.0.0"
        )
    
    def refresh_data(self):
        """Refresh all data in tabs"""
        # Refresh each tab
        try:
            # Let each tab refresh its data
            if hasattr(self.download_tab, 'refresh_video_list'):
                self.download_tab.refresh_video_list()
                
            if hasattr(self.process_tab, 'update_queue_display'):
                self.process_tab.update_queue_display()
                
            if hasattr(self.metadata_tab, 'update_videos_table'):
                self.metadata_tab.update_videos_table()
                
            if hasattr(self.upload_tab, 'update_queue_table'):
                self.upload_tab.update_queue_table()
            
            # Update status counts
            self.update_status_counts()
            
            # Update status
            self.status_label.setText("Data refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            QMessageBox.warning(self, "Refresh Error", f"Error refreshing data: {str(e)}")
    
    def confirm_clear_data(self):
        """Confirm and clear all application data"""
        reply = QMessageBox.question(
            self,
            "Clear All Data",
            "Are you sure you want to clear all application data?\n\n"
            "This will remove all videos, processing information, and metadata from the database.\n"
            "Downloaded videos will not be deleted from disk.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_data()
    
    def clear_data(self):
        """Clear all application data"""
        try:
            # Not actually implemented - in a real app, this would clear the database
            QMessageBox.information(
                self,
                "Clear Data",
                "Data clearing functionality will be implemented in a future version."
            )
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            QMessageBox.warning(self, "Clear Error", f"Error clearing data: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Confirm exit if processing is active
        if hasattr(self.process_tab, 'currently_processing') and self.process_tab.currently_processing:
            reply = QMessageBox.question(
                self,
                "Exit Confirmation",
                "Video processing is currently active. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Clean up resources
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Accept the close event
        event.accept()