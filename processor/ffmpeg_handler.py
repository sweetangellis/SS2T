import os
import subprocess
import json
import random
import time
from datetime import datetime

class FFmpegHandler:
    """
    Handles video processing using FFmpeg with a wide range of effects and filters.
    
    This class provides methods to apply various video enhancements, branding elements,
    content protection measures, and output customization as specified in the project requirements.
    """
    
    def __init__(self, config):
        """
        Initialize the FFmpeg handler.
        
        Args:
            config: Application configuration manager containing FFmpeg settings
        """
        self.config = config
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.output_dir = config.get("output_dir", "./output")
        self.watermarks_dir = config.get("watermarks_dir", "./watermarks")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Verify FFmpeg is available
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is available and get version information"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_info = result.stdout.split('\n')[0]
            print(f"Using FFmpeg: {version_info}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error verifying FFmpeg: {e}")
            print("Please ensure FFmpeg is installed and correctly configured in settings.")
            raise RuntimeError("FFmpeg not available")
    
    def process_video(self, input_path, channel_id=None, progress_callback=None):
        """
        Process a video with all enhancements and effects.
        
        Args:
            input_path: Path to the input video file
            channel_id: YouTube channel ID for channel-specific settings
            progress_callback: Callback function to report progress (0-100)
            
        Returns:
            output_path: Path to the processed video file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")
        
        # Get settings
        processing = self.config.get("processing", {})
        
        # Channel-specific settings
        channel_settings = {}
        if channel_id:
            channels = self.config.get("channels", {})
            if channel_id in channels:
                channel_settings = channels[channel_id]
        
        # Get watermark path
        watermark_path = None
        if channel_settings.get("watermark"):
            watermark_path = channel_settings["watermark"]
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(input_path)
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_processed_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Report progress
        if progress_callback:
            progress_callback(5)  # Starting
        
        # Build FFmpeg complex filter string with all effects
        filter_chains = []
        
        # Start with input
        filter_chains.append("[0:v]")
        
        # Report progress
        if progress_callback:
            progress_callback(10)  # Filter preparation
        
        # 1. Format standardization to 9:16 aspect ratio (1080x1920px)
        # First crop to remove any unwanted areas if needed
        # Then scale to the correct dimension
        filter_chains.append(f"scale=1080:1920:force_original_aspect_ratio=decrease")
        filter_chains.append(f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black")
        last_output = "v1"
        filter_chains.append(f"[{last_output}]")
        
        # 2. Apply visual enhancements
        # Color saturation adjustment
        color_saturation = processing.get("color_saturation", 1.2)
        filter_chains.append(f"[{last_output}]eq=saturation={color_saturation}")
        last_output = "v2"
        filter_chains.append(f"[{last_output}]")
        
        # Brightness correction
        brightness = processing.get("brightness", 1.1)
        filter_chains.append(f"[{last_output}]eq=brightness={brightness-1}")
        last_output = "v3"
        filter_chains.append(f"[{last_output}]")
        
        # Report progress
        if progress_callback:
            progress_callback(20)  # Basic enhancements applied
        
        # Opening zoom pulse effect
        zoom_pulse = processing.get("zoom_pulse", 1.05)
        filter_chains.append(f"[{last_output}]zoompan=z='min(zoom+0.0015,{zoom_pulse})':d=125:s=1080x1920")
        last_output = "v4"
        filter_chains.append(f"[{last_output}]")
        
        # Temporal denoising
        denoise_strength = processing.get("denoise_strength", 3)
        if denoise_strength > 0:
            filter_chains.append(f"[{last_output}]hqdn3d={denoise_strength}")
            last_output = "v5"
            filter_chains.append(f"[{last_output}]")
        
        # Sharpening filters
        sharpness = processing.get("sharpness", 1.5)
        if sharpness > 1.0:
            filter_chains.append(f"[{last_output}]unsharp=3:3:{sharpness}:3:3:{sharpness}")
            last_output = "v6"
            filter_chains.append(f"[{last_output}]")
        
        # Report progress
        if progress_callback:
            progress_callback(30)  # Visual enhancements applied
        
        # 3. Add branding elements (watermark)
        if watermark_path and os.path.exists(watermark_path):
            watermark_opacity = processing.get("watermark_opacity", 0.8)
            # Add watermark overlay
            filter_chains.append(f"[{last_output}][1:v]overlay=W-w-10:H-h-10:format=auto:alpha={watermark_opacity}")
            last_output = "v7"
            filter_chains.append(f"[{last_output}]")
        
            # Report progress
            if progress_callback:
                progress_callback(40)  # Watermark applied
        
        # Add subscribe arrow animation (placeholder for now)
        # This would be more complex and require an overlay image and animation timing
        # For now, we'll skip this feature
        
        # 4. Content protection measures
        # Speed randomization at video end
        speed_randomization = processing.get("speed_randomization", 0.05)
        if speed_randomization > 0:
            random_speed = 1.0 + (random.random() * speed_randomization)
            filter_chains.append(f"[{last_output}]setpts={1/random_speed}*PTS")
            last_output = "v8"
            filter_chains.append(f"[{last_output}]")
        
        # Subtle zoom factors
        zoom_factor = processing.get("zoom_factor", 1.02)
        if zoom_factor > 1.0:
            filter_chains.append(f"[{last_output}]scale=iw*{zoom_factor}:ih*{zoom_factor}")
            last_output = "v9"
            filter_chains.append(f"[{last_output}]")
        
        # Pixel shifting (slight position offset)
        pixel_shift = processing.get("pixel_shift", 1)
        if pixel_shift > 0:
            shift_x = random.randint(-pixel_shift, pixel_shift)
            shift_y = random.randint(-pixel_shift, pixel_shift)
            filter_chains.append(f"[{last_output}]crop=iw:ih:{shift_x}:{shift_y}")
            last_output = "v10"
            filter_chains.append(f"[{last_output}]")
        
        # Report progress
        if progress_callback:
            progress_callback(50)  # Protection measures applied
            
        # 5. Final output (remove the last label)
        filter_complex = "".join(filter_chains[:-1])
        
        # Build FFmpeg command
        command = [
            self.ffmpeg_path,
            "-y",  # Overwrite output files without asking
            "-i", input_path,  # Input video
        ]
        
        # Add watermark input if needed
        if watermark_path and os.path.exists(watermark_path):
            command.extend(["-i", watermark_path])
        
        # Add filter complex
        command.extend([
            "-filter_complex", filter_complex
        ])
        
        # Add audio options (normalize audio)
        if processing.get("audio_normalization", True):
            command.extend([
                "-af", "loudnorm=I=-16:LRA=11:TP=-1.5"
            ])
        
        # Add output options
        crf = processing.get("crf", 23)
        bitrate = processing.get("bitrate", "2M")
        threads = processing.get("threads", 4)
        
        command.extend([
            "-c:v", "libx264",  # Video codec
            "-preset", "medium",  # Encoding speed/compression ratio
            "-crf", str(crf),  # Quality
            "-b:v", bitrate,  # Bitrate
            "-c:a", "aac",  # Audio codec
            "-b:a", "192k",  # Audio bitrate
            "-threads", str(threads),  # Threading
            "-movflags", "+faststart",  # Web optimization
            output_path  # Output file
        ])
        
        # Report progress
        if progress_callback:
            progress_callback(60)  # Starting FFmpeg process
        
        # Execute FFmpeg command
        try:
            print(f"Running FFmpeg with command:\n{' '.join(command)}")
            
            # Start process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress by parsing FFmpeg output
            for line in process.stderr:
                if "time=" in line:
                    # Parse the time information to estimate progress
                    time_parts = line.split("time=")[1].split()[0].split(":")
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = float(time_parts[2])
                    
                    # Calculate total seconds
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    
                    # We'll need to know the duration of the video to calculate accurate progress
                    # For now, let's just report a simple estimate (60-90%)
                    progress = 60 + (total_seconds / 100)  # Simple estimate
                    progress = min(90, progress)  # Cap at 90%
                    
                    if progress_callback:
                        progress_callback(int(progress))
            
            # Wait for process to complete
            process.wait()
            
            # Check if successful
            if process.returncode != 0:
                error_output = process.stderr.read()
                raise RuntimeError(f"FFmpeg processing failed with error: {error_output}")
            
            # Generate a thumbnail for the processed video
            self._generate_thumbnail(output_path)
            
            # Report progress
            if progress_callback:
                progress_callback(100)  # Complete
            
            return output_path
            
        except Exception as e:
            print(f"Error processing video with FFmpeg: {e}")
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise
    
    def _generate_thumbnail(self, video_path):
        """Generate a thumbnail for the processed video"""
        if not os.path.exists(video_path):
            return None
            
        thumbnail_path = os.path.splitext(video_path)[0] + ".jpg"
        
        # Extract a frame at 10% into the video
        try:
            command = [
                self.ffmpeg_path,
                "-y",
                "-i", video_path,
                "-ss", "00:00:03",  # 3 seconds into the video
                "-frames:v", "1",
                thumbnail_path
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    def get_video_info(self, video_path):
        """
        Get information about a video file using FFprobe
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
            
        try:
            ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            
            command = [
                ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
            # Parse the JSON output
            info = json.loads(result.stdout)
            
            # Extract relevant information
            video_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
            audio_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
            
            if not video_streams:
                raise ValueError("No video stream found")
                
            # Get video info
            video_info = video_streams[0]
            format_info = info.get("format", {})
            
            # Build a simplified info dict
            return {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "width": int(video_info.get("width", 0)),
                "height": int(video_info.get("height", 0)),
                "codec": video_info.get("codec_name", ""),
                "fps": eval(video_info.get("r_frame_rate", "0/0")),
                "has_audio": len(audio_streams) > 0
            }
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None  
