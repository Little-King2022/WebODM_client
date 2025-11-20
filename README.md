# WebODM Client (v1.3.0)
<img width="1252" height="940" alt="image" src="https://github.com/user-attachments/assets/bad42984-ae9c-4026-82b6-55766fb1b76e" />

A Python and Tkinter-based [WebODM](https://github.com/OpenDroneMap/WebODM) client for batch management of projects and image stitching tasks in WebODM.

一个基于Python和Tkinter的[WebODM](https://github.com/OpenDroneMap/WebODM)客户端，用于批量管理WebODM中的项目和图片拼接任务。

[English](README.md) | [中文说明](README%20zh_CN.md)

## Features

- User Authentication: Connect to WebODM server and authenticate
- Project Management: View, create, and manage WebODM projects
- Task Management: Create, view, and manage tasks within selected projects
- Batch Operations: Support for batch operations on multiple tasks, such as downloading assets, restarting/canceling/deleting tasks
- Preset-Based Parameters: Load presets from `/api/presets/`; both task creation and restart send only preset options
- Background Uploads: Image uploads run in the background and auto commit; non-blocking UI
- Integrated Progress UI: Upload progress is shown inside the New Task dialog; the dialog can be minimized
- Multiple New Task Dialogs: Support opening multiple New Task dialogs concurrently, each with independent progress
- Credential Caching: Cache username and password to the local config for faster login (see Security Notes)

## Requirements

- Python 3.6+
- Dependencies: requests, tkinter, pillow, etc.

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the main program:

```bash
python main.py
```

2. Enter the WebODM server address in the interface (default is http://localhost:8000)
3. Click the "Login" button and enter your username and password (credentials will be cached locally after a successful login)
4. After successful login, you can view and manage projects and tasks

## Main Features

### Project Management

- View Project List: Automatically loads the project list after login
- Create New Project: Click the "New Project" button and enter the project name and description
- Select Project: Click on a project in the project list to load its task list

### Task Management

- View Task List: Automatically loads the task list after selecting a project
- Create New Task: Click the "New Task" button, select image files, choose a preset, and start. Uploads run in the background and will auto-commit. Upload progress is displayed inside the dialog, which can be minimized. You can open multiple New Task dialogs to run uploads concurrently.
- View Task Details: Double-click on a task in the task list to view detailed information

### Batch Operations

- Download Assets: Select one or more tasks, click the "Download Assets" button, choose the asset types to download and the save directory
- Restart Tasks: Select one or more tasks, click the "Restart Tasks" button and select a preset. Only preset options are sent.
- Cancel Tasks: Select one or more tasks, click the "Cancel Tasks" button to cancel pending or in-progress tasks
- Delete Tasks: Select one or more tasks, click the "Delete Tasks" button to delete the selected tasks

## Configuration File

The program creates a `.webodm_client` folder in the user's home directory to store configuration information, including server address, authentication token, and cached credentials (username and password) to streamline future logins.

### Security Notes
- Credential caching is enabled for convenience. If you prefer not to cache passwords, disable or remove the stored `password` in the config file.

## Notes

- This client needs to connect to a running WebODM server
- The default server address is http://localhost:8000, which can be modified in the interface
- Downloading large asset files may take a long time, please ensure you have enough disk space

## Snapshots
<img width="300" alt="image" src="https://github.com/user-attachments/assets/0a708b1e-7b04-4ab7-ae97-dc3725156c28" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/8eefda60-fde2-4dbd-b4b5-1542e44a78ef" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/8b1e8a7d-147a-4130-a4e7-485313af8f43" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/b037f80d-c215-43a3-9af5-7c74e8f9b23e" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/2da04c7a-2f57-43c1-b0d9-a6e12d81ae08" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/e959ae15-2509-4169-b925-a1b308ccd179" />
<img width="300" alt="image" src="https://github.com/user-attachments/assets/1e335bb6-d52f-499d-9d22-b366cb6a29b4" />






