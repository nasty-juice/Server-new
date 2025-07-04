# Project Blueberry (English)

## Overview

Blueberry is a Django-based web application designed to facilitate real-time matching and communication between users. The project leverages Django Channels for WebSocket communication, Celery for asynchronous task processing, and a variety of Django applications to handle different aspects of the system, including user authentication, chat, and various matching functionalities.

## Demo Video

<p align="center">
  <a href="https://youtu.be/B9iarRy1ys0">
    <img src="https://img.youtube.com/vi/B9iarRy1ys0/0.jpg" alt="Project Blueberry Demo Video Thumbnail" width="640" height="360" style="border-radius: 8px;">
  </a>
</p>

## System Architecture

The system is built around a central Django project with several interconnected applications. Here's a high-level overview of the architecture:

- **Web Server**: A WSGI/ASGI server (like Gunicorn/Daphne) handles HTTP and WebSocket requests.
- **Django Backend**: The core of the application, handling business logic, database interactions, and user authentication.
- **Database**: A relational database (SQLite) to store user data, chat messages, and matching information.
- **Redis**: Used as a message broker for both Celery and Django Channels, enabling real-time communication and background task processing.
- **Celery**: Manages asynchronous tasks such as sending notifications, processing matching queues, and handling time-based events.
- **Frontend**: A client-side application (likely a JavaScript framework like React or a mobile app) that interacts with the Django backend via REST APIs and WebSockets.

<p align="center">
  <img src="blueberry_sysarchi_diagram.png" alt="System Architecture Diagram" width="640" height="auto" style="border-radius: 8px;">
</p>

## Why These Technologies?

-   **Django**: Serves as the robust and scalable backend framework for Blueberry, providing the foundation for user management, matching logic, and API endpoints. Its "batteries-included" philosophy accelerates development of core features like authentication and database interactions.
-   **Django Channels**: Essential for Blueberry's real-time features, enabling instant chat messages between matched users and live updates on matching status. It allows the server to push data to clients without constant polling, creating a highly responsive user experience.
-   **Daphne**: As the ASGI server for Django Channels, Daphne efficiently handles the numerous concurrent WebSocket connections required for Blueberry's real-time chat and matching notifications. It ensures that the application remains responsive even under heavy real-time traffic.
-   **WebSockets**: The backbone of Blueberry's real-time communication. They provide persistent, low-latency connections for features like live chat rooms, real-time matching updates, and immediate notifications, significantly enhancing user interaction and engagement.
-   **Redis**: Utilized in Blueberry as the channel layer for Django Channels, facilitating seamless communication between different chat room instances and matching consumers. It also acts as the message broker for Celery, managing the queues for asynchronous tasks like background matching processes and timed notifications.
-   **Celery**: Powers Blueberry's asynchronous operations, such as executing complex matching algorithms in the background, sending delayed notifications (e.g., "chat room closing soon"), and managing the lifecycle of chat rooms. This offloads heavy processing from the main web server, ensuring a smooth and responsive user interface.
-   **django-allauth**: Provides a secure and comprehensive solution for user authentication and account management in Blueberry, including features like email verification and password reset, which are critical for a reliable user base.
-   **djangorestframework**: Enables Blueberry to expose well-structured RESTful APIs for its mobile or web frontend. This allows for clear separation of concerns and efficient data exchange for user profiles, matching preferences, and other application data.
-   **django-cors-headers**: Crucial for enabling secure cross-origin requests between Blueberry's frontend (which might be hosted on a different domain or port) and the Django backend, ensuring proper communication while adhering to web security standards.
-   **python-decouple**: Used in Blueberry to manage sensitive configurations (like API keys or database credentials) securely and flexibly. It allows environment-specific settings to be loaded without hardcoding them, which is vital for deployment across different environments (development, staging, production).

## Sequence Diagram: User Matching and Chat

This diagram illustrates the process of a user initiating a matching request, being matched with other users, and then entering a chat room.

<p align="center">
  <img src="blueberry_seq_diagram.png" alt="User Matching and Chat Sequence Diagram" width="640" height="auto" style="border-radius: 8px;">
</p>

## Applications

-   **my_app**: Core application for managing custom user models and related functionalities.
-   **my_auth**: Handles user authentication, registration, and profile management.
-   **chat**: Manages real-time chat functionality using Django Channels.
-   **matching**: Implements the logic for matching users based on specific criteria.
-   **matching2**: Appears to be another version or component of the matching system.
-   **taxi_matching**: A specific implementation for taxi-sharing matching.

## `matching` vs. `matching2`

This project contains two distinct but related Django applications for handling user matching: `matching` and `matching2`. Here’s a breakdown of their roles and the key differences.

### `my_site/matching/`

This application is a straightforward, real-time matching system for **individual users**.

*   **`consumer.py`**: The core of the application. It handles WebSocket connections for real-time communication. When a user wants to find a match, they are added to a queue for a specific location. Once enough users are in the queue, it initiates a match confirmation process.
*   **`models.py`**:
    *   `MatchingQueue`: Represents a waiting queue for a specific location.
    *   `MatchRequest`: A temporary model to manage a proposed match while waiting for users to accept or reject.
*   **`views.py`**: Contains views to render the HTML pages for the matching interface and an API endpoint to get the status of waiting queues.
*   **`urls.py`**: Defines the URL paths for the views and the WebSocket connection.
*   **`utils.py`**: Provides asynchronous helper functions for database operations, like getting or creating a matching queue.
*   **`tasks.py`**: Contains background tasks, such as deleting a chat room after a certain time.

**In short, `matching` is a system where individual users join a queue and are matched with other individuals in real-time.**

### `my_site/matching2/`

This is a more advanced version of the matching system, with a focus on **group matching** and a more complex workflow.

*   **`consumer.py`**: A much more sophisticated WebSocket consumer. It manages a friend invitation system, allowing users to form groups *before* entering a matching queue. It handles different matching categories (like meals and taxis) and broadcasts status updates. It also includes more robust error handling and connection management.
*   **`models.py`**:
    *   `InvitationRequest`: Stores friend invitations between users.
    *   `FriendGroup`: Represents a group of one or more users (a "solo" or "duo" group) that will enter the matching queue as a single unit.
*   **`match.py`**: This file separates the core matching logic from the consumer. It is responsible for handling the final match confirmation process after a queue is full, creating a chat room, and cleaning up the temporary groups and queues.
*   **`utils.py`**: Contains helper functions, including a `Timer` class for managing countdowns during the match confirmation phase.
*   **`apps.py`**: In addition to the standard setup, it includes a startup routine to clear out old data from Redis, which is used by Django Channels. This helps prevent issues with stale connections.

### Key Differences

1.  **Matching Unit**:
    *   `matching`: Matches **individual users**.
    *   `matching2`: Matches **pre-formed groups of users** (e.g., you and a friend).

2.  **Workflow**:
    *   `matching`: Simple workflow: join a queue -> wait for match -> confirm.
    *   `matching2`: More complex workflow: invite friend(s) -> form a group -> join a queue as a group -> wait for match -> confirm.

3.  **Features**:
    *   `matching2` has a full friend invitation system, which is absent in `matching`.
    *   `matching2` is designed to handle multiple matching categories (meals, taxis) and broadcast their status.
    *   `matching2` has more robust connection and state management, including better handling of user disconnections.

4.  **Code Structure**:
    *   `matching2` has a cleaner separation of concerns, with the core matching logic extracted into its own `match.py` file.

In conclusion, **`matching2` is an evolution of `matching`**. It expands on the original concept by introducing a social layer (friend invitations and groups) and creating a more scalable and feature-rich system. It reuses the `MatchingQueue` model from the `matching` app but in a more advanced way, by adding groups to it instead of individual users.

---

# 프로젝트 블루베리 (Korean)

## 개요

블루베리는 대학교 학생들이 쉽고 빠르게 학식메이트를 찾을 수 있게 해주고 지하철역에서 학교까지 같이 택시를 탑승할 택시메이트를 간편하게 찾을 수 있도록 해 경제적 부담을 줄일 수 있도록 설계된 Django 기반 웹 애플리케이션입니다. 이 프로젝트는 WebSocket 통신을 위한 Django Channels, 비동기 처리를 위한 Celery, 그리고 사용자 인증, 채팅, 다양한 매칭 기능 등 시스템의 여러 측면을 처리하기 위한 다양한 Django 애플리케이션을 활용합니다.

## 데모 비디오

<p align="center">
  <a href="https://youtu.be/B9iarRy1ys0">
    <img src="https://img.youtube.com/vi/B9iarRy1ys0/0.jpg" alt="Project Blueberry Demo Video Thumbnail" width="640" height="360" style="border-radius: 8px;">
  </a>
</p>

## 시스템 아키텍처

이 시스템은 여러 상호 연결된 애플리케이션으로 구성된 중앙 Django 프로젝트를 중심으로 구축됩니다. 다음은 아키텍처에 대한 개략적인 개요입니다.

-   **웹 서버**: WSGI/ASGI 서버(예: Gunicorn/Daphne)는 HTTP 및 WebSocket 요청을 처리합니다.
-   **Django 백엔드**: 비즈니스 로직, 데이터베이스 상호 작용 및 사용자 인증을 처리하는 애플리케이션의 핵심입니다.
-   **데이터베이스**: 사용자 데이터, 채팅 메시지 및 매칭 정보를 저장하는 관계형 데이터베이스(SQLite)입니다.
-   **Redis**: Celery 및 Django Channels 모두를 위한 메시지 브로커로 사용되어 실시간 통신 및 백그라운드 작업 처리를 가능하게 합니다.
-   **Celery**: 알림 전송, 매칭 큐 처리, 시간 기반 이벤트 처리와 같은 비동기 작업을 관리합니다.
-   **프론트엔드**: REST API 및 WebSockets를 통해 Django 백엔드와 상호 작용하는 클라이언트 측 애플리케이션(React 또는 모바일 앱과 같은 JavaScript 프레임워크일 가능성 높음)입니다.

<p align="center">
  <img src="blueberry_sysarchi_diagram.png" alt="시스템 아키텍처 다이어그램" width="640" height="auto" style="border-radius: 8px;">
</p>

## 이러한 기술을 사용하는 이유

-   **Django**: 블루베리의 사용자 관리, 매칭 로직 및 API 엔드포인트의 기반을 제공하는 강력하고 확장 가능한 백엔드 프레임워크 역할을 합니다. "배터리 포함" 철학은 인증 및 데이터베이스 상호 작용과 같은 핵심 기능 개발을 가속화합니다.
-   **Django Channels**: 블루베리의 실시간 기능에 필수적이며, 매칭된 사용자 간의 즉각적인 채팅 메시지와 매칭 상태에 대한 실시간 업데이트를 가능하게 합니다. 서버가 지속적인 폴링 없이 클라이언트에 데이터를 푸시할 수 있도록 하여 매우 반응적인 사용자 경험을 제공합니다.
-   **Daphne**: Django Channels의 ASGI 서버로서, Daphne는 블루베리의 실시간 채팅 및 매칭 알림에 필요한 수많은 동시 WebSocket 연결을 효율적으로 처리합니다. 이는 많은 실시간 트래픽에도 불구하고 애플리케이션이 반응성을 유지하도록 보장합니다.
-   **WebSockets**: 블루베리의 실시간 통신의 핵심입니다. 라이브 채팅방, 실시간 매칭 업데이트, 즉각적인 알림과 같은 기능에 지속적이고 낮은 지연 시간 연결을 제공하여 사용자 상호 작용 및 참여를 크게 향상시킵니다.
-   **Redis**: 블루베리에서 Django Channels의 채널 레이어로 활용되어 다양한 채팅방 인스턴스와 매칭 소비자 간의 원활한 통신을 용이하게 합니다. 또한 Celery의 메시지 브로커 역할을 하여 백그라운드 매칭 프로세스 및 시간 지정 알림과 같은 비동기 작업을 위한 큐를 관리합니다.
-   **Celery**: 복잡한 매칭 알고리즘을 백그라운드에서 실행하고, 지연된 알림(예: "채팅방 곧 종료")을 보내고, 채팅방의 수명 주기를 관리하는 등 블루베리의 비동기 작업을 지원합니다. 이는 주 웹 서버에서 무거운 처리를 오프로드하여 부드럽고 반응적인 사용자 인터페이스를 보장합니다.
-   **django-allauth**: 블루베리에서 사용자 인증 및 계정 관리를 위한 안전하고 포괄적인 솔루션을 제공하며, 신뢰할 수 있는 사용자 기반에 중요한 이메일 확인 및 비밀번호 재설정과 같은 기능을 포함합니다.
-   **djangorestframework**: 블루베리가 모바일 또는 웹 프론트엔드에 잘 구조화된 RESTful API를 노출할 수 있도록 합니다. 이를 통해 관심사 분리를 명확히 하고 사용자 프로필, 매칭 기본 설정 및 기타 애플리케이션 데이터에 대한 효율적인 데이터 교환이 가능합니다.
-   **django-cors-headers**: 블루베리의 프론트엔드(다른 도메인이나 포트에서 호스팅될 수 있음)와 Django 백엔드 간의 안전한 교차 출처 요청을 가능하게 하는 데 중요하며, 웹 보안 표준을 준수하면서 적절한 통신을 보장합니다.
-   **python-decouple**: 블루베리에서 민감한 구성(예: API 키 또는 데이터베이스 자격 증명)을 안전하고 유연하게 관리하는 데 사용됩니다. 환경별 설정을 하드코딩하지 않고 로드할 수 있도록 하여 다양한 환경(개발, 스테이징, 프로덕션)에 배포하는 데 필수적입니다.

## 시퀀스 다이어그램: 사용자 매칭 및 채팅

이 다이어그램은 사용자가 매칭 요청을 시작하고, 다른 사용자와 매칭된 다음, 채팅방에 입장하는 과정을 보여줍니다.

<p align="center">
  <img src="blueberry_seq_diagram.png" alt="사용자 매칭 및 채팅 시퀀스 다이어그램" width="640" height="auto" style="border-radius: 8px;">
</p>

## 애플리케이션

-   **my_app**: 사용자 정의 사용자 모델 및 관련 기능을 관리하기 위한 핵심 애플리케이션입니다.
-   **my_auth**: 사용자 인증, 등록 및 프로필 관리를 처리합니다.
-   **chat**: Django Channels를 사용하여 실시간 채팅 기능을 관리합니다.
-   **matching**: 특정 기준에 따라 사용자를 매칭하는 로직을 구현합니다.
-   **matching2**: 매칭 시스템의 다른 버전 또는 구성 요소입니다.
-   **taxi_matching**: 택시 공유 매칭을 위한 특정 구현입니다.

## `matching`과 `matching2` 비교

이 프로젝트에는 사용자 매칭을 처리하기 위한 두 개의 관련성 있는 Django 애플리케이션, `matching`과 `matching2`가 포함되어 있습니다. 각 애플리케이션의 역할과 주요 차이점은 다음과 같습니다.

### `my_site/matching/`

이 애플리케이션은 **개인 사용자**를 위한 간단한 실시간 매칭 시스템입니다.

*   **`consumer.py`**: 애플리케이션의 핵심입니다. 실시간 통신을 위해 WebSocket 연결을 처리합니다. 사용자가 매칭을 원하면 특정 위치의 대기열에 추가됩니다. 대기열에 충분한 사용자가 모이면 매칭 확인 프로세스를 시작합니다.
*   **`models.py`**:
    *   `MatchingQueue`: 특정 위치의 대기열을 나타냅니다.
    *   `MatchRequest`: 사용자가 수락 또는 거절을 기다리는 동안 제안된 매칭을 관리하는 임시 모델입니다.
*   **`views.py`**: 매칭 인터페이스를 위한 HTML 페이지를 렌더링하는 뷰와 대기열 상태를 가져오는 API 엔드포인트를 포함합니다.
*   **`urls.py`**: 뷰와 WebSocket 연결을 위한 URL 경로를 정의합니다.
*   **`utils.py`**: 매칭 대기열을 가져오거나 생성하는 등 데이터베이스 작업을 위한 비동기 헬퍼 함수를 제공합니다.
*   **`tasks.py`**: 일정 시간 후 채팅방을 삭제하는 등 백그라운드 작업을 포함합니다.

**요약하자면, `matching`은 개인 사용자가 대기열에 참여하여 다른 개인과 실시간으로 매칭되는 시스템입니다.**

### `my_site/matching2/`

이것은 **그룹 매칭**에 중점을 둔 고급 버전의 매칭 시스템으로, 더 복잡한 워크플로우를 가집니다.

*   **`consumer.py`**: 훨씬 더 정교한 WebSocket 컨슈머입니다. 친구 초대 시스템을 관리하여 사용자가 매칭 대기열에 들어가기 *전에* 그룹을 형성할 수 있도록 합니다. 식사 및 택시와 같은 다양한 매칭 카테고리를 처리하고 상태 업데이트를 브로드캐스트합니다. 또한 더 강력한 오류 처리 및 연결 관리를 포함합니다.
*   **`models.py`**:
    *   `InvitationRequest`: 사용자 간의 친구 초대장을 저장합니다.
    *   `FriendGroup`: 단일 단위로 매칭 대기열에 들어갈 한 명 이상의 사용자 그룹("솔로" 또는 "듀오" 그룹)을 나타냅니다.
*   **`match.py`**: 이 파일은 핵심 매칭 로직을 컨슈머에서 분리합니다. 대기열이 가득 찬 후 최종 매칭 확인 프로세스를 처리하고, 채팅방을 만들고, 임시 그룹 및 대기열을 정리하는 역할을 합니다.
*   **`utils.py`**: 매칭 확인 단계에서 카운트다운을 관리하기 위한 `Timer` 클래스를 포함한 헬퍼 함수를 포함합니다.
*   **`apps.py`**: 표준 설정 외에도 Django Channels에서 사용하는 Redis의 오래된 데이터를 정리하는 시작 루틴을 포함합니다. 이는 오래된 연결로 인한 문제를 방지하는 데 도움이 됩니다.

### 주요 차이점

1.  **매칭 단위**:
    *   `matching`: **개인 사용자**를 매칭합니다.
    *   `matching2`: **사전에 형성된 사용자 그룹**(예: 당신과 친구)을 매칭합니다.

2.  **워크플로우**:
    *   `matching`: 간단한 워크플로우: 대기열 참여 -> 매칭 대기 -> 확인.
    *   `matching2`: 더 복잡한 워크플로우: 친구 초대 -> 그룹 형성 -> 그룹으로 대기열 참여 -> 매칭 대기 -> 확인.

3.  **기능**:
    *   `matching2`에는 `matching`에는 없는 완전한 친구 초대 시스템이 있습니다.
    *   `matching2`는 여러 매칭 카테고리(식사, 택시)를 처리하고 상태를 브로드캐스트하도록 설계되었습니다.
    *   `matching2`는 사용자 연결 끊김을 더 잘 처리하는 등 더 강력한 연결 및 상태 관리를 제공합니다.

4.  **코드 구조**:
    *   `matching2`는 핵심 매칭 로직을 자체 `match.py` 파일로 추출하여 더 깔끔하게 관심사를 분리했습니다.

결론적으로, **`matching2`는 `matching`의 진화된 버전입니다.** 친구 초대 및 그룹이라는 소셜 레이어를 도입하고 더 확장 가능하고 기능이 풍부한 시스템을 만들어 원래 개념을 확장합니다. `matching` 앱의 `MatchingQueue` 모델을 재사용하지만 개별 사용자 대신 그룹을 추가하는 더 진보된 방식으로 사용합니다.
