document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const COURSE_ID = 'c-hackathon-d2';
    const USER_ID = 'usr-student-1';

    // Core Buttons & Containers
    const btnGenerateSummary = document.getElementById('btn-generate-summary');
    const btnBackToReading = document.getElementById('btn-back-to-reading');
    const readingState = document.getElementById('reading-state');
    const loadingState = document.getElementById('loading-state');
    const afterState = document.getElementById('after-state');
    
    // Header Buttons
    const btnHeaderBack = document.querySelector('.btn-back');
    const btnThemeToggle = document.querySelector('.theme-toggle');
    const btnLangToggle = document.querySelector('.lang-btn');

    // Sidebar elements
    const vlearnSidebar = document.getElementById('vlearn-sidebar');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    const docItems = document.querySelectorAll('.doc-item');

    // PDF Toolbar elements
    const toolBtns = document.querySelectorAll('.pdf-toolbar .tool-btn');
    const zoomLevelSpan = document.querySelector('.zoom-level');
    const mainPdfIframe = document.getElementById('main-pdf-iframe');
    let currentZoom = 100;
    let currentPdfUrl = "/data/vlearn-pack/slides/d2-slide-hackathon.pdf";

    // Popover & Slide Modal elements
    const popover = document.getElementById('node-popover');
    const popoverSlideNum = document.getElementById('popover-slide-num');
    const btnViewSlide = document.getElementById('btn-view-slide');
    const btnQuickFlashcard = document.getElementById('btn-quick-flashcard');
    const floatingActions = document.querySelector('.floating-actions');

    const slideModal = document.getElementById('slide-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const modalSlideTitle = document.getElementById('modal-slide-title');
    const btnPrevSlide = document.getElementById('btn-prev-slide');
    const btnNextSlide = document.getElementById('btn-next-slide');
    const modalSlideCounter = document.getElementById('modal-slide-counter');

    // History Modal elements
    const btnOpenHistory = document.getElementById('btn-open-history');
    const historyModal = document.getElementById('history-modal');
    const btnCloseHistory = document.getElementById('btn-close-history');

    // Chat Modal elements
    const btnOpenChat = document.querySelector('.vlearn-ai-btn');
    const chatModal = document.getElementById('chat-modal');
    const btnCloseChat = document.getElementById('btn-close-chat');
    const chatInput = document.getElementById('chat-input');
    const btnSendChat = document.getElementById('btn-send-chat');
    const chatMessagesContainer = document.getElementById('chat-messages-container');

    // Flashcard elements
    const demoFlashcard = document.getElementById('demo-flashcard');
    const fcQuestion = document.getElementById('fc-question');
    const fcOptions = document.getElementById('fc-options');
    const fcAnswer = document.getElementById('fc-answer');
    const fcCounter = document.getElementById('fc-counter');
    const fcTag = document.getElementById('fc-tag');
    const btnFcWrong = document.getElementById('btn-fc-wrong');
    const btnFcCorrect = document.getElementById('btn-fc-correct');

    // State Variables
    const TOTAL_SLIDES = 83;
    let currentSlidePage = 1;
    let currentlyHoveredSlideInfo = "";
    let selectedNodeId = null;
    let currentChatSessionId = null;

    let flashcardList = [];
    let currentCardIdx = 0;
    let quizCompleted = false;

    // 1. HEADER BUTTON HANDLERS
    if (btnHeaderBack) {
        btnHeaderBack.addEventListener('click', () => {
            if (afterState && afterState.classList.contains('active')) {
                afterState.classList.remove('active');
                readingState.classList.add('active');
                if (floatingActions) floatingActions.classList.remove('hidden');
            } else {
                alert("Bạn đang ở trang bài giảng VLearn.");
            }
        });
    }

    if (btnThemeToggle) {
        btnThemeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const icon = btnThemeToggle.querySelector('i');
            if (icon) {
                if (document.body.classList.contains('dark-mode')) {
                    icon.className = 'fas fa-sun';
                } else {
                    icon.className = 'far fa-moon';
                }
            }
        });
    }

    if (btnLangToggle) {
        btnLangToggle.addEventListener('click', () => {
            btnLangToggle.textContent = btnLangToggle.textContent === 'VI' ? 'EN' : 'VI';
        });
    }

    // 2. SIDEBAR HANDLERS (Accordion & Document Selection)
    if (btnToggleSidebar && vlearnSidebar) {
        btnToggleSidebar.addEventListener('click', () => {
            vlearnSidebar.classList.toggle('collapsed');
        });
    }

    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            const body = item.querySelector('.accordion-body');
            const icon = header.querySelector('.acc-icon');
            
            if (body) {
                body.classList.toggle('hidden');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down');
                    icon.classList.toggle('fa-chevron-up');
                }
            }
        });
    });

    docItems.forEach(item => {
        item.addEventListener('click', (e) => {
            docItems.forEach(d => d.classList.remove('active'));
            item.classList.add('active');

            const pdfPath = item.getAttribute('data-pdf');
            const docTitle = item.getAttribute('data-title');
            
            if (pdfPath && mainPdfIframe) {
                currentPdfUrl = pdfPath;
                mainPdfIframe.src = `${pdfPath}#page=1&toolbar=0&navpanes=0&scrollbar=0`;
            }

            const headerDocTitle = document.querySelector('.doc-title');
            if (headerDocTitle && docTitle) {
                headerDocTitle.innerHTML = `${docTitle} <i class="fas fa-check-circle" style="color: #2563eb; font-size: 12px; margin-left: 4px;"></i>`;
            }
        });
    });

    // 3. PDF TOOLBAR HANDLERS (Zoom, Tool Select, Fullscreen, Download)
    toolBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const icon = btn.querySelector('i');
            if (!icon) return;

            // Zoom In (+)
            if (icon.classList.contains('fa-plus')) {
                if (currentZoom < 200) currentZoom += 25;
                if (zoomLevelSpan) zoomLevelSpan.textContent = `${currentZoom}%`;
                if (mainPdfIframe) mainPdfIframe.style.transform = `scale(${currentZoom / 100})`;
            }
            // Zoom Out (-)
            else if (icon.classList.contains('fa-minus')) {
                if (currentZoom > 50) currentZoom -= 25;
                if (zoomLevelSpan) zoomLevelSpan.textContent = `${currentZoom}%`;
                if (mainPdfIframe) mainPdfIframe.style.transform = `scale(${currentZoom / 100})`;
            }
            // Fullscreen
            else if (icon.classList.contains('fa-expand')) {
                const pdfContainer = document.querySelector('.pdf-page-container');
                if (pdfContainer) {
                    if (!document.fullscreenElement) {
                        pdfContainer.requestFullscreen().catch(err => alert(`Lỗi fullscreen: ${err.message}`));
                    } else {
                        document.exitFullscreen();
                    }
                }
            }
            // Download PDF
            else if (icon.classList.contains('fa-file-download')) {
                const a = document.createElement('a');
                a.href = currentPdfUrl;
                a.download = currentPdfUrl.split('/').pop() || 'slide.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
            // Select Tool
            else if (btn.textContent.trim().length > 0) {
                toolBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    });

    // 4. API FETCH HELPER WITH RETRY
    async function apiFetch(endpoint, options = {}, retries = 2) {
        const url = `${API_BASE_URL}${endpoint}`;
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const response = await fetch(url, {
                    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
                    ...options
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            } catch (err) {
                if (attempt === retries) throw err;
                await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
            }
        }
    }

    // 5. SESSION RESUMING
    function checkResumeSession() {
        const savedState = localStorage.getItem('vlearn_session_state');
        if (savedState) {
            try {
                const parsed = JSON.parse(savedState);
                if (parsed.activeState === 'after') {
                    readingState.classList.remove('active');
                    afterState.classList.add('active');
                    if (floatingActions) floatingActions.classList.add('hidden');
                    loadMindmapAndFlashcards();
                }
            } catch (e) {}
        }
    }

    function saveSessionState(stateName) {
        localStorage.setItem('vlearn_session_state', JSON.stringify({
            activeState: stateName,
            courseId: COURSE_ID,
            userId: USER_ID,
            selectedNodeId: selectedNodeId,
            timestamp: new Date().toISOString()
        }));
    }

    // 6. SUMMARY GENERATION & PROGRESS
    if (btnGenerateSummary) {
        btnGenerateSummary.addEventListener('click', async () => {
            if (vlearnSidebar) vlearnSidebar.classList.add('collapsed');
            if (floatingActions) floatingActions.classList.add('hidden');
            
            readingState.classList.remove('active');
            loadingState.classList.add('active');
            const loadingText = document.getElementById('loading-text');

            try {
                if (loadingText) loadingText.textContent = "Đang phân tích 83 trang slide...";
                await new Promise(r => setTimeout(r, 500));

                if (loadingText) loadingText.textContent = "Đang trích xuất khái niệm & cấu trúc Mindmap...";
                await apiFetch('/learning/summary/generate', {
                    method: 'POST',
                    body: JSON.stringify({ course_id: COURSE_ID, user_id: USER_ID })
                });

                if (loadingText) loadingText.textContent = "Đang tạo bộ Flashcard & tiến trình học tập...";
                await new Promise(r => setTimeout(r, 500));

                await loadMindmapAndFlashcards();

                loadingState.classList.remove('active');
                afterState.classList.add('active');
                saveSessionState('after');
            } catch (err) {
                alert(`Lỗi khi khởi tạo summary: ${err.message}`);
                loadingState.classList.remove('active');
                readingState.classList.add('active');
                if (floatingActions) floatingActions.classList.remove('hidden');
            }
        });
    }

    if (btnBackToReading) {
        btnBackToReading.addEventListener('click', () => {
            afterState.classList.remove('active');
            readingState.classList.add('active');
            if (floatingActions) floatingActions.classList.remove('hidden');
            saveSessionState('reading');
        });
    }

    // 7. MINDMAP & FLASHCARD LOADING
    async function loadMindmapAndFlashcards() {
        try {
            const mindmapData = await apiFetch(`/learning/mindmaps/${COURSE_ID}?user_id=${USER_ID}`);
            renderMindmapTree(mindmapData.tree);

            const flashcardsData = await apiFetch(`/learning/flashcards/${COURSE_ID}`);
            flashcardList = flashcardsData;
            currentCardIdx = 0;
            quizCompleted = false;
            renderFlashcard(currentCardIdx);
        } catch (err) {
            console.warn("Backend API disconnected, using fallback mock data:", err);
        }
    }

    function renderMindmapTree(treeData) {
        const container = document.querySelector('.tree');
        if (!container || !treeData || treeData.length === 0) return;

        function buildNodeHTML(node, isRoot = false) {
            const nodeClass = isRoot ? "node root-node" : "node";
            const slideAttr = node.slide_ref || "Slide X";
            const hasChildren = node.children && node.children.length > 0;
            
            let nodeStatusClass = "";
            let badgeHTML = "";
            
            if (node.completion_percentage !== undefined) {
                if (node.completion_percentage === 100) {
                    nodeStatusClass = " node-completed";
                } else if (node.completion_percentage >= 50) {
                    nodeStatusClass = " node-in-progress";
                } else if (node.completion_percentage > 0) {
                    nodeStatusClass = " node-needs-work";
                }
                
                if (node.completion_percentage > 0) {
                    badgeHTML = `<div class="node-progress-badge">${node.completion_percentage}%</div>`;
                }
            }

            let html = `<li>`;
            html += `<div class="${nodeClass}${nodeStatusClass}" data-id="${node.id}" data-slide="${slideAttr}" data-pct="${node.completion_percentage || 0}">
                        ${badgeHTML}
                        ${node.label}
                        ${hasChildren ? '<i class="fas fa-chevron-down toggle-tree-icon" style="margin-left:6px; font-size:10px; opacity:0.7;"></i>' : ''}
                     </div>`;

            if (hasChildren) {
                html += `<ul>`;
                node.children.forEach(child => {
                    html += buildNodeHTML(child, false);
                });
                html += `</ul>`;
            }
            html += `</li>`;
            return html;
        }

        container.innerHTML = `<ul>${buildNodeHTML(treeData[0], true)}</ul>`;
        attachMindmapNodeEvents();
    }

    function attachMindmapNodeEvents() {
        const nodes = document.querySelectorAll('.tree .node');
        nodes.forEach(node => {
            node.addEventListener('mouseenter', () => {
                const slideInfo = node.getAttribute('data-slide');
                selectedNodeId = node.getAttribute('data-id');
                const pct = parseFloat(node.getAttribute('data-pct') || 0);
                
                if (popoverSlideNum) popoverSlideNum.textContent = slideInfo;
                currentlyHoveredSlideInfo = slideInfo;
                
                const btnPersonalize = document.getElementById('btn-personalize-flashcard');
                if (btnPersonalize) {
                    if (pct > 0 && pct < 100) {
                        btnPersonalize.classList.remove('hidden');
                    } else {
                        btnPersonalize.classList.add('hidden');
                    }
                }
                
                const mindmapContainer = document.querySelector('.mindmap-container');
                if (!mindmapContainer || !popover) return;

                const rect = node.getBoundingClientRect();
                const containerRect = mindmapContainer.getBoundingClientRect();
                
                popover.style.display = 'block';
                popover.classList.remove('hidden');
                
                const popoverWidth = popover.offsetWidth;
                const popoverHeight = popover.offsetHeight;
                
                const topPosition = rect.top - containerRect.top + mindmapContainer.scrollTop - popoverHeight - 10;
                const leftPosition = rect.left - containerRect.left + mindmapContainer.scrollLeft + (rect.width / 2) - (popoverWidth / 2);
                
                popover.style.top = `${topPosition}px`;
                popover.style.left = `${leftPosition}px`;
                popover.style.pointerEvents = 'auto';
            });

            const toggleIcon = node.querySelector('.toggle-tree-icon');
            if (toggleIcon) {
                toggleIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const subTree = node.nextElementSibling;
                    if (subTree && subTree.tagName === 'UL') {
                        subTree.classList.toggle('hidden');
                        toggleIcon.classList.toggle('fa-chevron-down');
                        toggleIcon.classList.toggle('fa-chevron-right');
                    }
                });
            }
        });
    }

    if (popover) {
        popover.addEventListener('mouseleave', () => {
            popover.classList.add('hidden');
            popover.style.pointerEvents = 'none';
            setTimeout(() => {
                if (popover.classList.contains('hidden')) popover.style.display = 'none';
            }, 200);
        });
    }

    // 8. FLASHCARD & QUIZ INTERACTIVE LOGIC
    let currentMode = 'review'; // 'review' or 'quiz'
    let currentNodeIdFilter = null; // null for full course (30 questions), or node_id for branch (5 questions)
    let currentBatchAttempts = {}; // { card_id: is_correct }
    let historyLogList = [
        {
            date: "Hôm nay",
            title: "Day 02: Xác định bài toán AI (Toàn bài - Flashcard)",
            statusHtml: '<span class="badge-status" style="background:#dcfce7; color:#166534;">Hoàn thành 100%</span>'
        }
    ];

    const btnModeReview = document.getElementById('btn-mode-review');
    const btnModeQuiz = document.getElementById('btn-mode-quiz');
    const btnResetCourseCards = document.getElementById('btn-reset-course-cards');
    const btnQuickQuiz = document.getElementById('btn-quick-quiz');
    const btnSubmitBatch = document.getElementById('btn-submit-batch');
    const cardPanelTitle = document.getElementById('card-panel-title');

    function showToast(message) {
        let toast = document.querySelector('.vl-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'vl-toast';
            document.body.appendChild(toast);
        }
        toast.innerHTML = `<i class="fas fa-check-circle" style="color:#22c55e;"></i> <span>${message}</span>`;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3500);
    }

    function renderHistoryModalTable() {
        const tbody = document.getElementById('history-table-body');
        if (!tbody) return;
        tbody.innerHTML = historyLogList.map((item, idx) => `
            <tr class="${idx === 0 ? 'active-row' : ''}">
                <td style="font-size:12px; color:var(--vl-text-sub); white-space:nowrap;">${item.date}</td>
                <td style="font-weight:600; color:var(--vl-text-main);">${item.title}</td>
                <td>${item.statusHtml}</td>
            </tr>
        `).join('');
    }

    async function loadFlashcardsOrQuizzes(mode, nodeId = null) {
        currentMode = mode;
        currentNodeIdFilter = nodeId;
        currentBatchAttempts = {};

        if (btnModeReview && btnModeQuiz) {
            if (mode === 'review') {
                btnModeReview.className = 'btn-sm btn-primary';
                btnModeQuiz.className = 'btn-sm btn-outline';
            } else {
                btnModeQuiz.className = 'btn-sm btn-primary';
                btnModeReview.className = 'btn-sm btn-outline';
            }
        }

        if (cardPanelTitle) {
            const scopeText = nodeId ? "Nhánh chọn (5 câu)" : "Toàn bài (30 câu)";
            cardPanelTitle.textContent = mode === 'review' ? `Ôn tập · ${scopeText}` : `Take Quiz · ${scopeText}`;
        }

        try {
            let url = `/learning/flashcards/${COURSE_ID}?mode=${mode}`;
            if (nodeId) url += `&node_id=${nodeId}`;
            const cards = await apiFetch(url);
            flashcardList = cards || [];
            currentCardIdx = 0;
            quizCompleted = false;
            renderFlashcard(currentCardIdx);
        } catch (e) {
            console.warn("Failed to load flashcards/quiz:", e);
        }
    }

    function submitBatchResults() {
        if (!flashcardList || flashcardList.length === 0) return;

        const totalCards = flashcardList.length;
        const correctCount = Object.values(currentBatchAttempts).filter(v => v === true).length;
        const batchAccuracy = totalCards > 0 ? Math.round((correctCount / totalCards) * 100) : 100;
        
        // Update Mindmap Node Badge directly on DOM
        if (currentNodeIdFilter) {
            const nodeEl = document.querySelector(`.tree .node[data-id="${currentNodeIdFilter}"]`);
            if (nodeEl) {
                nodeEl.setAttribute('data-pct', batchAccuracy);
                nodeEl.classList.remove('node-completed', 'node-in-progress', 'node-needs-work');
                
                let statusClass = 'node-needs-work';
                if (batchAccuracy === 100) statusClass = 'node-completed';
                else if (batchAccuracy >= 50) statusClass = 'node-in-progress';
                nodeEl.classList.add(statusClass);

                let badgeEl = nodeEl.querySelector('.node-progress-badge');
                if (!badgeEl) {
                    badgeEl = document.createElement('div');
                    badgeEl.className = 'node-progress-badge';
                    nodeEl.prepend(badgeEl);
                }
                badgeEl.textContent = `${batchAccuracy}%`;

                nodeEl.classList.remove('node-updated-pulse');
                void nodeEl.offsetWidth;
                nodeEl.classList.add('node-updated-pulse');
            }
        } else {
            const rootNode = document.querySelector('.tree .root-node');
            if (rootNode) {
                let badgeEl = rootNode.querySelector('.node-progress-badge');
                if (!badgeEl) {
                    badgeEl = document.createElement('div');
                    badgeEl.className = 'node-progress-badge';
                    rootNode.prepend(badgeEl);
                }
                badgeEl.textContent = `${batchAccuracy}%`;
                rootNode.classList.remove('node-updated-pulse');
                void rootNode.offsetWidth;
                rootNode.classList.add('node-updated-pulse');
            }
        }

        // Header progress update
        const valCompletion = document.getElementById('val-completion');
        const valMastery = document.getElementById('val-mastery');
        if (valCompletion) valCompletion.textContent = `${batchAccuracy}%`;
        if (valMastery) valMastery.textContent = `${batchAccuracy}%`;

        // History Log Record Update
        let scopeLabel = "Day 02: Toàn bài";
        if (currentNodeIdFilter) {
            const nodeEl = document.querySelector(`.tree .node[data-id="${currentNodeIdFilter}"]`);
            if (nodeEl) {
                const clone = nodeEl.cloneNode(true);
                const badge = clone.querySelector('.node-progress-badge');
                if (badge) badge.remove();
                scopeLabel = `Day 02: ${clone.textContent.replace(/\s+/g, ' ').trim()}`;
            }
        }
        const modeLabel = currentMode === 'review' ? 'Flashcard' : 'Quiz';
        const fullTitle = `${scopeLabel} (${modeLabel})`;

        let statusHtml = `<span class="badge-status" style="background:#fee2e2; color:#991b1b;">Cần cố gắng ${batchAccuracy}%</span>`;
        if (batchAccuracy >= 80) {
            statusHtml = `<span class="badge-status" style="background:#dcfce7; color:#166534;">Hoàn thành ${batchAccuracy}%</span>`;
        } else if (batchAccuracy >= 50) {
            statusHtml = `<span class="badge-status" style="background:#fefce8; color:#854d0e;">Đang ôn ${batchAccuracy}%</span>`;
        }

        const timeNow = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + " (Hôm nay)";
        
        historyLogList.unshift({
            date: timeNow,
            title: fullTitle,
            statusHtml: statusHtml
        });

        // Update Mini History panel on main page
        const miniHistoryText = document.getElementById('mini-history-text');
        if (miniHistoryText) {
            miniHistoryText.innerHTML = `Vừa xong: <strong>${fullTitle}</strong> · <strong>${batchAccuracy}%</strong> <i class="fas fa-chevron-right ml-4"></i>`;
        }

        // Render History modal table
        renderHistoryModalTable();

        // Completion Card View
        if (fcQuestion) {
            fcQuestion.innerHTML = `<span class='text-success'><i class='fas fa-trophy'></i> Đã nộp bài thành công!</span>`;
        }
        if (fcOptions) {
            fcOptions.innerHTML = `
                <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 12px;">
                    <div style="font-size: 24px; font-weight: 700; color: #15803d;">${batchAccuracy}%</div>
                    <div style="font-size: 12px; color: #166534;">Trả lời đúng ${correctCount} / ${totalCards} câu hỏi (${currentMode === 'review' ? 'Flashcard' : 'Quiz'})</div>
                </div>
                <button id="btn-submit-again" class="btn-sm btn-primary full-width"><i class="fas fa-redo"></i> Luyện lại bộ này</button>
            `;
            const btnSubmitAgain = document.getElementById('btn-submit-again');
            if (btnSubmitAgain) {
                btnSubmitAgain.addEventListener('click', () => loadFlashcardsOrQuizzes(currentMode, currentNodeIdFilter));
            }
        }
        if (fcAnswer) {
            fcAnswer.textContent = `Kết quả ${batchAccuracy}% đã được ghi nhận vào Lịch sử học và hiển thị trực tiếp lên Mindmap!`;
        }

        quizCompleted = true;
        showToast(`🎉 Nộp bài thành công! % Hoàn thành: ${batchAccuracy}%`);
    }

    if (btnSubmitBatch) {
        btnSubmitBatch.addEventListener('click', submitBatchResults);
    }

    if (btnModeReview) {
        btnModeReview.addEventListener('click', () => loadFlashcardsOrQuizzes('review', currentNodeIdFilter));
    }

    if (btnModeQuiz) {
        btnModeQuiz.addEventListener('click', () => loadFlashcardsOrQuizzes('quiz', currentNodeIdFilter));
    }

    if (btnResetCourseCards) {
        btnResetCourseCards.addEventListener('click', () => loadFlashcardsOrQuizzes(currentMode, null));
    }

    if (btnQuickFlashcard) {
        btnQuickFlashcard.addEventListener('click', async () => {
            if (popover) popover.classList.add('hidden');
            if (selectedNodeId) {
                await loadFlashcardsOrQuizzes('review', selectedNodeId);
            }
        });
    }

    if (btnQuickQuiz) {
        btnQuickQuiz.addEventListener('click', async () => {
            if (popover) popover.classList.add('hidden');
            if (selectedNodeId) {
                await loadFlashcardsOrQuizzes('quiz', selectedNodeId);
            }
        });
    }

    const btnPersonalizeFlashcard = document.getElementById('btn-personalize-flashcard');
    if (btnPersonalizeFlashcard) {
        btnPersonalizeFlashcard.addEventListener('click', async () => {
            if (popover) popover.classList.add('hidden');
            if (selectedNodeId) {
                try {
                    const personalizedCards = await apiFetch('/learning/flashcards/personalize', {
                        method: 'POST',
                        body: JSON.stringify({
                            user_id: USER_ID,
                            course_id: COURSE_ID,
                            node_id: selectedNodeId
                        })
                    });
                    if (personalizedCards && personalizedCards.length > 0) {
                        flashcardList = personalizedCards;
                        currentCardIdx = 0;
                        quizCompleted = false;
                        renderFlashcard(currentCardIdx);
                    }
                } catch(e) {}
            }
        });
    }

    const btnCardPrev = document.getElementById('btn-card-prev');
    const btnCardNext = document.getElementById('btn-card-next');
    const fcClickHint = document.getElementById('fc-click-hint');

    function renderFlashcard(idx) {
        if (!flashcardList || flashcardList.length === 0) {
            if (fcQuestion) fcQuestion.textContent = "Không có dữ liệu thẻ.";
            if (fcOptions) fcOptions.innerHTML = "";
            if (fcAnswer) fcAnswer.textContent = "";
            return;
        }

        // Show btnFcWrong and btnFcCorrect ONLY for Flashcard mode ('review')! Hide for Quiz mode ('quiz')!
        if (btnFcWrong && btnFcCorrect) {
            const isReview = (currentMode === 'review');
            btnFcWrong.style.display = isReview ? 'inline-flex' : 'none';
            btnFcCorrect.style.display = isReview ? 'inline-flex' : 'none';
        }

        if (idx >= flashcardList.length) {
            const modeName = currentMode === 'review' ? 'Flashcard' : 'Quiz';
            if (fcQuestion) fcQuestion.innerHTML = `<span class='text-success'><i class='fas fa-trophy'></i> Hoàn thành bài ${modeName}!</span>`;
            if (fcOptions) fcOptions.innerHTML = `
                <div style='text-align:center; padding: 12px;'>
                    <button id='btn-submit-batch-final' class='btn-sm btn-primary full-width' style='padding: 8px 16px;'><i class='fas fa-check-double'></i> Nộp bài & Cập nhật % Mindmap</button>
                </div>
            `;
            if (fcAnswer) fcAnswer.innerHTML = `Tuyệt vời! Bạn đã trả lời xong ${flashcardList.length} câu ${modeName}. Nhấn Nộp bài để tính điểm và cập nhật % lên Mindmap!`;
            if (fcCounter) fcCounter.innerHTML = `<i class="fas fa-layer-group"></i> ${flashcardList.length} / ${flashcardList.length} Thẻ`;
            
            const btnFinal = document.getElementById('btn-submit-batch-final');
            if (btnFinal) {
                btnFinal.addEventListener('click', submitBatchResults);
            }
            return;
        }

        const card = flashcardList[idx];
        const modeBadge = currentMode === 'review' ? "Flashcard" : "Quiz";
        if (fcTag) fcTag.textContent = `${card.tag || "Khái niệm"} (${modeBadge})`;
        if (fcQuestion) fcQuestion.textContent = card.question;
        
        // Ensure card starts un-flipped on card render
        if (demoFlashcard && demoFlashcard.classList.contains('flipped')) {
            demoFlashcard.classList.remove('flipped');
        }

        // Toggle click hint visibility based on mode
        if (fcClickHint) {
            fcClickHint.style.display = currentMode === 'review' ? 'block' : 'none';
        }

        if (fcOptions) {
            if (card.options && card.options.length > 0) {
                if (currentMode === 'quiz') {
                    fcOptions.innerHTML = card.options.map((opt) => {
                        const safeOpt = opt.replace(/"/g, '&quot;');
                        return `<button class="mcq-opt-btn" data-opt="${safeOpt}">${opt}</button>`;
                    }).join('');

                    const optBtns = fcOptions.querySelectorAll('.mcq-opt-btn');
                    optBtns.forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const selectedOpt = btn.getAttribute('data-opt');
                            handleQuizOptionClick(btn, selectedOpt, card, optBtns);
                        });
                    });
                } else {
                    fcOptions.innerHTML = card.options.map(opt => `<div class="mcq-opt">${opt}</div>`).join('');
                }
            } else {
                fcOptions.innerHTML = "";
            }
        }

        if (fcAnswer) fcAnswer.textContent = card.answer;
        if (fcCounter) fcCounter.innerHTML = `<i class="fas fa-layer-group"></i> ${idx + 1} / ${flashcardList.length} ${modeBadge}`;

        // Update Prev and Next navigation buttons state
        if (btnCardPrev) {
            btnCardPrev.disabled = (idx <= 0);
            btnCardPrev.style.opacity = btnCardPrev.disabled ? '0.3' : '1';
            btnCardPrev.style.cursor = btnCardPrev.disabled ? 'not-allowed' : 'pointer';
        }
        if (btnCardNext) {
            btnCardNext.disabled = (idx >= flashcardList.length - 1);
            btnCardNext.style.opacity = btnCardNext.disabled ? '0.3' : '1';
            btnCardNext.style.cursor = btnCardNext.disabled ? 'not-allowed' : 'pointer';
        }
    }

    function handleQuizOptionClick(clickedBtn, selectedOpt, card, allBtns) {
        allBtns.forEach(b => b.disabled = true);

        const normSelected = String(selectedOpt).trim();
        const normAnswer = String(card.answer).trim();
        
        const isCorrect = normSelected === normAnswer || 
                          normAnswer.includes(normSelected) || 
                          normSelected.includes(normAnswer) ||
                          (normSelected[0] && normAnswer[0] && normSelected[0] === normAnswer[0]);

        if (isCorrect) {
            clickedBtn.classList.add('opt-correct');
            clickedBtn.innerHTML += ` <i class="fas fa-check-circle ml-4"></i>`;
            handleFlashcardAttempt(true, selectedOpt);
        } else {
            clickedBtn.classList.add('opt-wrong');
            clickedBtn.innerHTML += ` <i class="fas fa-times-circle ml-4"></i>`;
            
            allBtns.forEach(b => {
                const bOpt = String(b.getAttribute('data-opt')).trim();
                if (bOpt === normAnswer || normAnswer.includes(bOpt) || (bOpt[0] && normAnswer[0] && bOpt[0] === normAnswer[0])) {
                    b.classList.add('opt-correct');
                }
            });
            handleFlashcardAttempt(false, selectedOpt);
        }
    }

    if (demoFlashcard) {
        demoFlashcard.addEventListener('click', () => {
            if (currentMode === 'review') {
                demoFlashcard.classList.toggle('flipped');
            }
        });
    }

    if (btnCardPrev) {
        btnCardPrev.addEventListener('click', () => {
            if (currentCardIdx > 0) {
                if (demoFlashcard) demoFlashcard.classList.remove('flipped');
                currentCardIdx--;
                renderFlashcard(currentCardIdx);
            }
        });
    }

    if (btnCardNext) {
        btnCardNext.addEventListener('click', () => {
            if (currentCardIdx < flashcardList.length - 1) {
                if (demoFlashcard) demoFlashcard.classList.remove('flipped');
                currentCardIdx++;
                renderFlashcard(currentCardIdx);
            }
        });
    }

    async function handleFlashcardAttempt(isCorrect, selectedOption = null) {
        if (quizCompleted || flashcardList.length === 0) return;

        const currentCard = flashcardList[currentCardIdx];
        if (currentCard) {
            const cardId = currentCard.id || `card-${currentCardIdx}`;
            currentBatchAttempts[cardId] = isCorrect;
        }
        
        try {
            const result = await apiFetch('/progress/attempts', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: USER_ID,
                    flashcard_id: currentCard.id || "fc-default-1",
                    is_correct: isCorrect,
                    selected_option: selectedOption || currentCard.answer,
                    response_time_ms: 1200
                })
            });

            const valCompletion = document.getElementById('val-completion');
            const valMastery = document.getElementById('val-mastery');
            const tokenTag = document.getElementById('progress-token-tag');

            if (valCompletion && result.completion_percentage !== undefined) {
                valCompletion.textContent = `${result.completion_percentage.toFixed(0)}%`;
            }
            if (valMastery && result.mastery_percentage !== undefined) {
                valMastery.textContent = `${result.mastery_percentage.toFixed(0)}%`;
            }
            if (tokenTag && result.progress_token) {
                tokenTag.textContent = result.progress_token;
            }
        } catch (e) {}
    }

    if (btnFcWrong) {
        btnFcWrong.addEventListener('click', () => {
            handleFlashcardAttempt(false);
            if (currentCardIdx < flashcardList.length - 1) {
                if (demoFlashcard) demoFlashcard.classList.remove('flipped');
                currentCardIdx++;
                renderFlashcard(currentCardIdx);
            }
        });
    }

    if (btnFcCorrect) {
        btnFcCorrect.addEventListener('click', () => {
            handleFlashcardAttempt(true);
            if (currentCardIdx < flashcardList.length - 1) {
                if (demoFlashcard) demoFlashcard.classList.remove('flipped');
                currentCardIdx++;
                renderFlashcard(currentCardIdx);
            }
        });
    }

    // 9. HISTORY MODAL HANDLERS
    if (btnOpenHistory && historyModal && btnCloseHistory) {
        btnOpenHistory.addEventListener('click', () => {
            renderHistoryModalTable();
            historyModal.classList.remove('hidden');
        });
        btnCloseHistory.addEventListener('click', () => historyModal.classList.add('hidden'));
    }

    // 10. SLIDE MODAL VIEWER
    if (btnViewSlide) {
        btnViewSlide.addEventListener('click', () => {
            openSlideModal(currentlyHoveredSlideInfo);
        });
    }

    function parseSlidePageNumber(slideInfoStr) {
        if (!slideInfoStr) return 1;
        if (slideInfoStr === "Toàn bộ bài") return 1;
        const match = String(slideInfoStr).match(/\d+/);
        if (match) {
            const page = parseInt(match[0], 10);
            if (!isNaN(page) && page >= 1 && page <= TOTAL_SLIDES) {
                return page;
            }
        }
        return 1;
    }

    function openSlideModal(slideInfoStr) {
        currentSlidePage = parseSlidePageNumber(slideInfoStr);
        updateModalContent();
        
        if (slideModal) slideModal.classList.remove('hidden');
        if (popover) {
            popover.classList.add('hidden');
            popover.style.pointerEvents = 'none';
        }
    }

    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => slideModal.classList.add('hidden'));
    }

    if (btnNextSlide) {
        btnNextSlide.addEventListener('click', () => {
            if (currentSlidePage < TOTAL_SLIDES) {
                currentSlidePage++;
                updateModalContent();
            }
        });
    }

    if (btnPrevSlide) {
        btnPrevSlide.addEventListener('click', () => {
            if (currentSlidePage > 1) {
                currentSlidePage--;
                updateModalContent();
            }
        });
    }

    function updateModalContent() {
        if (currentSlidePage < 1) currentSlidePage = 1;
        if (currentSlidePage > TOTAL_SLIDES) currentSlidePage = TOTAL_SLIDES;

        if (modalSlideTitle) modalSlideTitle.textContent = `Nguồn: Slide ${currentSlidePage}`;
        
        const pdfIframe = document.getElementById('pdf-iframe');
        const pdfSrc = `${currentPdfUrl}#page=${currentSlidePage}&toolbar=0&navpanes=0&scrollbar=0`;
        if (pdfIframe) pdfIframe.src = pdfSrc;
        if (mainPdfIframe) mainPdfIframe.src = pdfSrc;
        
        if (modalSlideCounter) modalSlideCounter.textContent = `${currentSlidePage} / ${TOTAL_SLIDES}`;
        
        if (btnPrevSlide) {
            btnPrevSlide.disabled = (currentSlidePage <= 1);
            btnPrevSlide.style.opacity = btnPrevSlide.disabled ? '0.3' : '1';
            btnPrevSlide.style.cursor = btnPrevSlide.disabled ? 'not-allowed' : 'pointer';
        }
        if (btnNextSlide) {
            btnNextSlide.disabled = (currentSlidePage >= TOTAL_SLIDES);
            btnNextSlide.style.opacity = btnNextSlide.disabled ? '0.3' : '1';
            btnNextSlide.style.cursor = btnNextSlide.disabled ? 'not-allowed' : 'pointer';
        }
    }

    // 11. TUTOR AGENT CHAT INTEGRATION
    if (btnOpenChat) {
        btnOpenChat.addEventListener('click', async () => {
            if (chatModal) chatModal.classList.remove('hidden');
            if (!currentChatSessionId) {
                try {
                    const session = await apiFetch('/chat/sessions', {
                        method: 'POST',
                        body: JSON.stringify({
                            user_id: USER_ID,
                            course_id: COURSE_ID,
                            title: "Chat với Tutor AI"
                        })
                    });
                    currentChatSessionId = session.session_id;
                } catch (e) {}
            }
        });
    }

    if (btnCloseChat) {
        btnCloseChat.addEventListener('click', () => {
            if (chatModal) chatModal.classList.add('hidden');
        });
    }

    async function sendChatMessage() {
        const questionText = chatInput ? chatInput.value.trim() : "";
        if (!questionText) return;

        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'chat-msg user-msg';
        userMsgDiv.style.cssText = 'background: #eff6ff; padding: 10px 14px; border-radius: 8px; font-size: 13px; color: var(--vl-text-main); align-self: flex-end; max-width: 85%;';
        userMsgDiv.textContent = questionText;
        chatMessagesContainer.appendChild(userMsgDiv);
        chatInput.value = '';
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

        const loadingMsgDiv = document.createElement('div');
        loadingMsgDiv.className = 'chat-msg tutor-thinking';
        loadingMsgDiv.style.cssText = 'background: #f8fafc; padding: 10px 14px; border-radius: 8px; font-size: 13px; color: var(--vl-text-sub);';
        loadingMsgDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Tutor AI đang tìm câu trả lời từ tài liệu...';
        chatMessagesContainer.appendChild(loadingMsgDiv);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

        try {
            const res = await apiFetch('/chat/messages', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: USER_ID,
                    course_id: COURSE_ID,
                    question: questionText,
                    selected_node_id: selectedNodeId,
                    conversation_id: currentChatSessionId
                })
            });

            loadingMsgDiv.remove();

            const tutorMsgDiv = document.createElement('div');
            tutorMsgDiv.className = 'chat-msg tutor-msg';
            tutorMsgDiv.style.cssText = 'background: #f8fafc; padding: 12px 16px; border-radius: 8px; font-size: 13px; color: var(--vl-text-main); border: 1px solid var(--vl-border); align-self: flex-start; max-width: 90%;';
            
            let htmlContent = `<div><strong><i class="fas fa-robot" style="color: var(--vl-primary);"></i> Tutor AI:</strong></div>`;
            htmlContent += `<div style="margin-top: 6px; line-height: 1.5;">${res.answer}</div>`;

            if (res.citations && res.citations.length > 0) {
                htmlContent += `<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--vl-border); font-size: 11px; color: var(--vl-text-sub);">
                    <i class="fas fa-file-pdf"></i> <strong>Nguồn trích dẫn:</strong> `;
                res.citations.forEach(cit => {
                    const slideNum = cit.page_number || cit.slide_number || 1;
                    htmlContent += `<a href="#" class="chat-citation-link" data-page="${slideNum}" style="color: var(--vl-primary); font-weight: 600; margin-right: 8px; text-decoration: underline;">[Slide ${slideNum}]</a>`;
                });
                htmlContent += `</div>`;
            }

            tutorMsgDiv.innerHTML = htmlContent;
            chatMessagesContainer.appendChild(tutorMsgDiv);
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

            tutorMsgDiv.querySelectorAll('.chat-citation-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const page = link.getAttribute('data-page');
                    openSlideModal(`Slide ${page}`);
                });
            });

        } catch (e) {
            loadingMsgDiv.remove();
            const errDiv = document.createElement('div');
            errDiv.style.cssText = 'background: #fef2f2; color: #991b1b; padding: 10px 14px; border-radius: 8px; font-size: 13px;';
            errDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> Không thể kết nối với Tutor Agent. <button class="btn-sm btn-outline retry-chat-btn" style="margin-left: 8px;">Thử lại</button>`;
            chatMessagesContainer.appendChild(errDiv);

            errDiv.querySelector('.retry-chat-btn').addEventListener('click', () => {
                errDiv.remove();
                sendChatMessage();
            });
        }
    }

    if (btnSendChat) btnSendChat.addEventListener('click', sendChatMessage);
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }

    // INITIALIZATION
    checkResumeSession();
    loadMindmapAndFlashcards();
});
