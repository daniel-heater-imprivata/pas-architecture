# RDP Converter Architecture

## Overview

The RDP Converter is a specialized component that converts audit files from RDP sessions into video formats for playback and analysis. It processes the binary audit data captured during RDP sessions and generates MP4 video files that can be viewed using standard video players.

## Core Responsibilities

### Audit File Processing
- **Binary Parsing**: Parse proprietary audit file formats from RDP sessions
- **Video Generation**: Convert audit data into standard video formats (MP4, AVI)
- **Audio Processing**: Handle audio streams captured during RDP sessions
- **Metadata Extraction**: Extract session metadata and timing information

### Video Production
- **Frame Rendering**: Render RDP protocol data into video frames
- **Compression**: Apply video compression for efficient storage and playback
- **Quality Control**: Maintain video quality while optimizing file size
- **Format Support**: Support multiple output video formats and codecs

## Technical Architecture

### Technology Stack
- **Language**: C/C++ for performance-critical video processing
- **Video Libraries**: FFmpeg for video encoding and processing
- **RDP Libraries**: FreeRDP for RDP protocol parsing and rendering
- **Build System**: CMake for cross-platform builds
- **Deployment**: Native binary with RPM packaging

### Module Structure
```
rdp-converter/
├── cli/                # Command-line interface and main application
├── resource/           # Resource files and configuration templates
├── rpm/               # RPM packaging configuration
├── bin/               # Binary output and deployment scripts
└── *.c, *.h          # Core C implementation files
```

### Key Components

#### Audit File Parser
- **File Format**: Parse proprietary audit file format
- **Data Extraction**: Extract RDP protocol data and metadata
- **Error Handling**: Handle corrupted or incomplete audit files
- **Validation**: Validate audit file integrity and completeness

#### RDP Protocol Handler
- **Protocol Parsing**: Parse RDP protocol messages and commands
- **Graphics Rendering**: Render RDP graphics commands into video frames
- **Input Processing**: Process keyboard and mouse input events
- **Channel Handling**: Handle RDP virtual channels and data streams

#### Video Encoder
- **Frame Generation**: Generate video frames from RDP graphics data
- **Encoding**: Encode frames using H.264 or other video codecs
- **Audio Synchronization**: Synchronize audio streams with video
- **Output Generation**: Generate final video files in requested formats

## Core Files and Functions

### Main Components
- **`sl_auditfile.c/h`**: Audit file parsing and data extraction
- **`sl_chapterfile.c/h`**: Chapter file handling for session segmentation
- **`sl_ffmpeg.c/h`**: FFmpeg integration for video encoding
- **`sl_transport.c`**: Transport layer for data handling
- **`sl_utils.c/h`**: Utility functions and helper routines

### RDP Integration
- **`xf_client.c/h`**: Main RDP client implementation
- **`xf_gdi.c/h`**: Graphics Device Interface for rendering
- **`xf_graphics.c/h`**: Graphics processing and frame generation
- **`xf_input.c/h`**: Input event processing
- **`xf_channels.c/h`**: RDP channel handling

### Video Processing
- **`xf_video.c/h`**: Video frame processing and generation
- **`xf_gfx.c/h`**: Advanced graphics processing
- **`xf_monitor.c/h`**: Multi-monitor support and handling

## Processing Workflow

### Input Processing
1. **Audit File Validation**: Validate input audit file format and integrity
2. **Metadata Extraction**: Extract session metadata, timing, and configuration
3. **Data Parsing**: Parse RDP protocol data and commands
4. **Chapter Processing**: Process session chapters and segments

### Video Generation
1. **Frame Rendering**: Render RDP graphics commands into video frames
2. **Audio Processing**: Process and synchronize audio streams
3. **Video Encoding**: Encode frames using specified video codec
4. **Output Generation**: Generate final video file with metadata

### Quality Control
1. **Frame Validation**: Validate generated video frames for quality
2. **Synchronization Check**: Verify audio/video synchronization
3. **File Integrity**: Verify output file integrity and completeness
4. **Metadata Embedding**: Embed session metadata in video file

## Command-Line Interface

### Basic Usage
```bash
# Convert RDP audit file to MP4 video
rdp-converter -i session.audit -o session.mp4

# Specify video quality and codec
rdp-converter -i session.audit -o session.mp4 -q high -c h264

# Convert with custom resolution and frame rate
rdp-converter -i session.audit -o session.mp4 -r 1920x1080 -f 30
```

### Advanced Options
```bash
# Convert with audio processing
rdp-converter -i session.audit -o session.mp4 -a enable

# Generate multiple formats
rdp-converter -i session.audit -o session.mp4 -f mp4,avi,webm

# Process chapter segments separately
rdp-converter -i session.audit -o session_%d.mp4 -chapters
```

## Configuration Options

### Video Settings
```ini
[video]
codec = h264
quality = medium
resolution = auto
framerate = 15
bitrate = 1000k

[audio]
enabled = true
codec = aac
bitrate = 128k
samplerate = 44100
```

### Processing Options
```ini
[processing]
threads = auto
memory_limit = 1GB
temp_directory = /tmp/rdp-converter
cleanup = true

[output]
format = mp4
metadata = true
chapters = false
```

## Performance Characteristics

### Processing Speed
- **Conversion Rate**: Typically 2-5x real-time processing speed
- **Memory Usage**: Configurable memory limits for large files
- **CPU Utilization**: Multi-threaded processing for optimal CPU usage
- **Disk I/O**: Efficient disk I/O with configurable temporary storage

### Scalability
- **Batch Processing**: Support for batch conversion of multiple files
- **Parallel Processing**: Parallel processing of multiple audit files
- **Resource Management**: Configurable resource limits and throttling
- **Queue Management**: Processing queue for large-scale conversions

### Quality Metrics
- **Video Quality**: Configurable quality settings for different use cases
- **File Size**: Optimized compression for storage efficiency
- **Compatibility**: Output compatible with standard video players
- **Metadata Preservation**: Preserve session metadata in video files

## Integration Points

### Audit System Integration
- **File Location**: Automatic discovery of audit files for conversion
- **Metadata Sync**: Synchronize conversion status with audit database
- **Cleanup**: Automatic cleanup of processed audit files
- **Error Reporting**: Report conversion errors to audit system

### Web Interface Integration
- **Conversion Requests**: Handle conversion requests from web interface
- **Progress Reporting**: Report conversion progress and status
- **File Delivery**: Deliver converted video files for download
- **Thumbnail Generation**: Generate video thumbnails for preview

### Storage Integration
- **File Management**: Manage converted video files and storage
- **Retention Policies**: Apply retention policies to converted videos
- **Backup Integration**: Integration with backup and archival systems
- **Access Control**: Apply access controls to converted video files

## Deployment and Operations

### Installation
```bash
# Install RPM package
sudo rpm -ivh rdp-converter-1.0.0.rpm

# Configure system service
sudo systemctl enable rdp-converter
sudo systemctl start rdp-converter
```

### Configuration Management
- **System Configuration**: System-wide configuration in `/etc/rdp-converter/`
- **User Configuration**: User-specific configuration and preferences
- **Environment Variables**: Environment-based configuration overrides
- **Runtime Configuration**: Runtime configuration changes without restart

### Monitoring and Logging
- **Process Monitoring**: Monitor conversion processes and resource usage
- **Error Logging**: Comprehensive error logging and reporting
- **Performance Metrics**: Collect performance metrics and statistics
- **Health Checks**: Regular health checks and status reporting

## Current Implementation Status

### Completed Features
- **Core Conversion**: Complete RDP audit file to video conversion
- **Multiple Formats**: Support for MP4, AVI, and other video formats
- **Audio Support**: Audio stream processing and synchronization
- **Command-Line Interface**: Full-featured command-line interface

### Known Limitations
- **File Size Limits**: Performance degradation with very large audit files
- **Memory Usage**: High memory usage for complex RDP sessions
- **Error Recovery**: Limited error recovery for corrupted audit files
- **Format Support**: Limited support for newer RDP protocol features

### Performance Optimization
- **Multi-Threading**: Multi-threaded processing for improved performance
- **Memory Management**: Optimized memory usage and garbage collection
- **Disk I/O**: Efficient disk I/O and temporary file management
- **Codec Optimization**: Optimized video codec settings for quality and size

## Future Enhancements

### Planned Improvements
- **Web Interface**: Web-based interface for conversion management
- **API Integration**: REST API for programmatic conversion requests
- **Cloud Support**: Support for cloud-based storage and processing
- **Real-Time Conversion**: Real-time conversion during session recording

### Technology Upgrades
- **Modern Codecs**: Support for newer video codecs (H.265, AV1)
- **GPU Acceleration**: GPU-accelerated video encoding for improved performance
- **Container Support**: Containerized deployment and orchestration
- **Microservice Architecture**: Decomposition into microservice components

---

*This document describes the current implementation of the RDP Converter component. For proposed improvements and modernization strategies, see the [recommendations](../recommendations/) section.*
