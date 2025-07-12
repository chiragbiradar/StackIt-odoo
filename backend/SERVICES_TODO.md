# StackIt Backend Services - TODO List

## 🎯 **MVP Services (2 Hours Sprint)**

### ⏰ **Time Allocation**
- **Total Time:** 2 hours
- **Priority:** Core Q&A functionality only
- **Goal:** Working demo for hackathon

---

## 📋 **Services To Implement**

### 1. **Question Service** ⭐ **CRITICAL** - [ ] TODO
**File:** `services/question_service.py`  
**Time:** 45 minutes  
**Priority:** 1 (Highest)

**Endpoints:**
- [ ] `POST /questions` - Create new question
  - Required: title, description, tags, author_id
  - Validation: title length, description not empty
- [ ] `GET /questions` - List all questions
  - Pagination: skip, limit
  - Sorting: by created_at DESC
  - Include: author info, tag names, answer count
- [ ] `GET /questions/{id}` - Get question details
  - Include: full question, all answers, author info
  - Include: vote counts, accepted answer

**Schemas Needed:**
- [ ] `schemas/question.py` - QuestionCreate, QuestionResponse, QuestionList

---

### 2. **Answer Service** ⭐ **CRITICAL** - [ ] TODO
**File:** `services/answer_service.py`  
**Time:** 30 minutes  
**Priority:** 2

**Endpoints:**
- [ ] `POST /answers` - Create answer for question
  - Required: content, question_id, author_id
  - Validation: content not empty, question exists
- [ ] `PUT /answers/{id}/accept` - Accept answer (question owner only)
  - Authorization: only question author can accept
  - Business logic: unaccept previous answer, accept new one

**Schemas Needed:**
- [ ] `schemas/answer.py` - AnswerCreate, AnswerResponse

---

### 3. **Vote Service** ⭐ **CRITICAL** - [ ] TODO
**File:** `services/vote_service.py`  
**Time:** 30 minutes  
**Priority:** 3

**Endpoints:**
- [ ] `POST /answers/{id}/vote` - Upvote/downvote answer
  - Body: {"is_upvote": true/false}
  - Business logic: prevent self-voting, update existing vote
  - Update: answer vote_score, user reputation
- [ ] `DELETE /answers/{id}/vote` - Remove vote
  - Remove user's vote on answer
  - Update: answer vote_score, user reputation

**Schemas Needed:**
- [ ] `schemas/vote.py` - VoteCreate, VoteResponse

---

### 4. **Tag Service** 🔧 **SUPPORTING** - [ ] TODO
**File:** `services/tag_service.py`  
**Time:** 10 minutes  
**Priority:** 4

**Endpoints:**
- [ ] `GET /tags` - List all available tags
  - Simple list for question creation form
  - Include: id, name, usage_count

**Schemas Needed:**
- [ ] `schemas/tag.py` - TagResponse

---

### 5. **User Service** 🔧 **SUPPORTING** - [ ] TODO
**File:** `services/user_service.py`  
**Time:** 5 minutes  
**Priority:** 5 (Lowest)

**Endpoints:**
- [ ] `GET /users/{id}` - Get user profile
  - Basic info: username, full_name, bio, reputation
  - Stats: questions_count, answers_count

**Schemas Needed:**
- [ ] `schemas/user.py` - UserProfile (reuse existing UserResponse)

---

## 🚀 **Implementation Checklist**

### **Phase 1: Question Service (45 min)**
- [ ] Create `schemas/question.py`
- [ ] Create `services/question_service.py`
- [ ] Add router to `server.py`
- [ ] Test: Create question, list questions, get question details

### **Phase 2: Answer Service (30 min)**
- [ ] Create `schemas/answer.py`
- [ ] Create `services/answer_service.py`
- [ ] Add router to `server.py`
- [ ] Test: Create answer, accept answer

### **Phase 3: Vote Service (30 min)**
- [ ] Create `schemas/vote.py`
- [ ] Create `services/vote_service.py`
- [ ] Add router to `server.py`
- [ ] Test: Vote on answer, remove vote

### **Phase 4: Supporting Services (15 min)**
- [ ] Create `schemas/tag.py`
- [ ] Create `services/tag_service.py`
- [ ] Create `services/user_service.py`
- [ ] Add routers to `server.py`
- [ ] Test: Get tags, get user profile

---

## ❌ **NOT Implementing (Out of Scope)**

- Comments system
- Real-time notifications
- Advanced search
- File uploads
- Rich text editor
- User profile editing
- Admin features
- Email verification
- Password reset

---

## 🎯 **Success Criteria**

After 2 hours, the platform should support:
- ✅ User registration/login
- ✅ Ask questions with tags
- ✅ Answer questions
- ✅ Vote on answers (upvote/downvote)
- ✅ Accept best answers
- ✅ View user profiles
- ✅ Browse questions and answers

**Demo Flow:**
1. Register user → Login
2. Create question with tags
3. Another user answers
4. Vote on answer
5. Accept answer
6. Browse questions

---

## 📝 **Notes**

- Keep schemas simple (no complex validation)
- Use basic error handling
- Focus on core functionality over edge cases
- Hardcode some data if needed for demo
- Test each service as you build it
