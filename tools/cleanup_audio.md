# Audio Cleanup Script Documentation

`cleanup_audio.py` is a utility script designed to manage disk space by automatically removing old audio files and directories from the bot's storage.

## Overview

The script scans the designated audio folder and deletes any content that exceeds a specified age (retention period). It is designed to work with a directory structure where audio files are organized into subfolders (typically by date).

## Configuration

The script relies on the following variables from `config.py`:

*   `AUDIO_FOLDER`: A `pathlib.Path` object pointing to the root directory where audio files are stored.
*   `AUDIO_CLEANUP_DAYS`: An integer representing the number of days to retain files. Files older than this value will be deleted.

## Key Functions

### `cleanup_old_audio()`

The primary function that executes the cleanup logic:

1.  **Validation**: Ensures the `AUDIO_FOLDER` exists and `AUDIO_CLEANUP_DAYS` is greater than 0.
2.  **Cutoff Calculation**: Determines the timestamp cutoff (current time minus retention days in seconds).
3.  **Directory Traversal**:
    *   Iterates through each subfolder in `AUDIO_FOLDER`.
    *   If a subfolder's modification time is older than the cutoff, the entire folder and its contents are removed using `shutil.rmtree`.
    *   If the folder is newer, the script iterates through individual files within it and deletes those that have exceeded the retention period.
4.  **Logging**: Provides status updates and error reporting via the standard `logging` module.

## Usage

The script can be executed directly as a standalone process or scheduled as a cron job/task:

```bash
python tools/cleanup_audio.py
```

When run directly, it initializes basic logging at the `INFO` level to report the number of folders or files removed.
