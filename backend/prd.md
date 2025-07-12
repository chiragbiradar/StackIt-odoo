# StackIt – A Minimal Q&A Forum Platform

## Overview

StackIt is a minimal question-and-answer platform that supports collaborative learning and structured knowledge sharing. It’s designed to be simple, user-friendly, and focused on the core experience of asking and answering questions within a community.

## Tech Stack

### Backend Framework
- **FastAPI**: High-performance, modern Python web framework with automatic API documentation and type hints support

### Database
- **PostgreSQL**: Robust, scalable relational database with excellent performance and ACID compliance

### Caching
- **Disk-based caching**: Efficient file-system based caching for improved performance and reduced database load

### Real-time Notifications
- **py-pg-notify**: PostgreSQL-based real-time notification system ([py-pg-notify](https://pypi.org/project/py-pg-notify/))
  - Leverages PostgreSQL's LISTEN/NOTIFY for efficient real-time updates
  - Minimal overhead and excellent integration with existing database infrastructure

## User Roles

| Role  | Permissions |
|-------|-------------|
| **Guest** | View all questions and answers |
| **User** | Register, log in, post questions/answers, vote |
| **Admin** | Moderate content |

## Core Features (Must-Have)

### 1. Ask Question

Users can submit a new question using:
- **Title**: Short and descriptive
- **Description**: Written using a rich text editor
- **Tags**: Multi-select input (e.g., React, JWT)

### 2. Rich Text Editor Features

The description editor should support:
- **Text Formatting**: Bold, Italic, Strikethrough
- **Lists**: Numbered lists, Bullet points
- **Media**: Emoji insertion, Image upload
- **Links**: Hyperlink insertion (URL)
- **Alignment**: Text alignment – Left, Center, Right

### 3. Answering Questions

- Users can post answers to any question
- Answers can be formatted using the same rich text editor
- Only logged-in users can post answers

### 4. Voting & Accepting Answers

- Users can upvote or downvote answers
- Question owners can mark one answer as accepted

### 5. Tagging

- Questions must include relevant tags
- Tags help categorize and filter content

### 6. Notification System

- A notification icon (bell) appears in the top navigation bar
- Users are notified when:
  - Someone answers their question
  - Someone comments on their answer
  - Someone mentions them using @username
- The icon shows the number of unread notifications
- Clicking the icon opens a dropdown with recent notifications