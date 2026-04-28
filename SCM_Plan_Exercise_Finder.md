# Software Configuration Management (SCM) Plan: Exercise Finder

## 1. Introduction
This document presents the Software Configuration Management (SCM) Plan for the **Exercise Finder** project. The purpose of this plan is to ensure that all the components of the software, such as documents, source code, and test cases, are properly managed and controlled throughout the development process. Since software development involves continuous changes and updates, having an SCM plan helps in maintaining consistency and avoiding confusion among team members. This document acts as a guideline for managing changes in a systematic and organized manner.

## 2. Scope
The scope of this SCM plan includes identifying all the important components of the project, maintaining their different versions, and ensuring that any changes made are properly reviewed and approved. It also includes defining how the project will handle updates, track progress, and maintain records of all modifications. The plan is applicable to all phases of the Exercise Finder, from requirement analysis to final deployment.

## 3. SCM Objectives
The main objective of this SCM plan is to maintain the integrity and consistency of the software throughout its lifecycle. It aims to track every change made to the system so that errors can be minimized and previous versions can be restored if required. Another important objective is to improve collaboration among team members by ensuring that everyone is working on the correct and updated version of the project. Overall, SCM helps in improving the quality and reliability of the software.

## 4. Configuration Items (CIs)
| CI ID | Item Name | Description |
| :--- | :--- | :--- |
| CI-01 | SRS Document | Requirements specification for Exercise Finder |
| CI-02 | Design Document | System architecture, UI wireframes & database design |
| CI-03 | Source Code | Python (Flask), HTML, CSS, and JS files |
| CI-04 | Test Cases | Unit tests, Integration tests, and API test results |
| CI-05 | Database Schema | SQLite tables, relationships, and migration scripts |
| CI-06 | User Manual | Documentation for users on how to search and track exercises |

## 5. Version Control Plan
For managing different versions of the project, a version control system such as Git is used. All project files are stored in a central repository, allowing team members to access and update them easily.

1.  **Tool Used**: Git / GitHub
2.  **Repository Name**: `Exercise-Finder`
3.  **Version Naming Convention**:
    *   **v1.0**: Initial release (MVP)
    *   **v1.1**: Minor updates (Bug fixes, UI tweaks)
    *   **v2.0**: Major updates (New core features like AI recommendations)
4.  **Branching Strategy**:
    *   **main**: Stable version, production-ready code.
    *   **dev**: Development branch for integration testing.
    *   **feature-***: Dedicated branches for individual features (e.g., `feature-auth`, `feature-tracker`).

## 6. Change Management Process
Any modification in the project follows a defined change management process to avoid unnecessary errors and ensure smooth project progress.

### Steps to be followed:
1.  **Change Request (CR) Submission**: Describe the required modification.
2.  **Impact Analysis**: Understand how the change affects the rest of the system.
3.  **Approval by Project Lead**: Decide whether to proceed with the change.
4.  **Implementation**: Developer writes the code.
5.  **Testing**: Thorough verification of the new code.
6.  **Update Version**: Update the version number if necessary.
7.  **Release**: Deploy the updated version.

### Change Request Format Example:
| CR ID | Description | Priority | Status |
| :--- | :--- | :--- | :--- |
| CR-01 | Implement BMI/BMR calculator | High | Approved |

## 7. Configuration Status Accounting
To keep track of all activities, configuration status accounting is maintained. This involves recording details such as the current version of each component, the changes made, the date of modification, and the person responsible.

### Example Record:
| CI | Version | Updated By | Date |
| :--- | :--- | :--- | :--- |
| Source Code | v1.1 | Developer | 28-04-2026 |

## 8. Configuration Audit
Configuration audits are conducted at regular intervals to ensure quality:
*   **Functional Audits**: Verify whether the system meets the SRS requirements (e.g., exercise searching works correctly).
*   **Physical Audits**: Ensure all necessary components (README, `.env` template, database scripts) are present and correctly implemented.

## 9. Build and Release Management
Builds are created after completing significant features. Each build is documented with release notes. Older stable versions are archived on GitHub as "Releases" to allow for quick restoration if issues arise in the current build.

## 10. Tools Used
*   **GitHub**: Version Control and Collaboration.
*   **VS Code**: Primary Integrated Development Environment (IDE).
*   **SQLite**: Database management (local/dev).
*   **Python/Flask**: Backend framework.

## 11. Roles and Responsibilities
| Role | Responsibility |
| :--- | :--- |
| Project Manager | Approves change requests and signs off on releases. |
| Developer | Implements code changes and manages feature branches. |
| Tester | Conducts unit and integration testing on the `dev` branch. |
| SCM Manager | Maintains version integrity and repository organization. |

## 12. Backup and Recovery Plan
To prevent data loss:
1.  **Regular Commits**: Code is pushed to GitHub daily.
2.  **Database Backups**: Periodic snapshots of `exercise_finder.db`.
3.  **GitHub Availability**: Ensures all versions are available online.
4.  **Rollback Procedure**: In case of critical failure, the system can be restored to the previous stable tag on the `main` branch.
