document.addEventListener('DOMContentLoaded', () => {
    // Buttons & States
    const btnGenerateSummary = document.getElementById('btn-generate-summary');
    const btnBackToReading = document.getElementById('btn-back-to-reading');
    const readingState = document.getElementById('reading-state');
    const loadingState = document.getElementById('loading-state');
    const afterState = document.getElementById('after-state');
    
    // Sidebar elements
    const vlearnSidebar = document.getElementById('vlearn-sidebar');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    
    // Mindmap nodes
    const nodes = document.querySelectorAll('.node');
    const popover = document.getElementById('node-popover');
    const popoverSlideNum = document.getElementById('popover-slide-num');
    const btnViewSlide = document.getElementById('btn-view-slide');
    const btnQuickFlashcard = document.getElementById('btn-quick-flashcard');
    const floatingActions = document.querySelector('.floating-actions');

    // Modal elements
    const slideModal = document.getElementById('slide-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const modalSlideTitle = document.getElementById('modal-slide-title');
    const btnPrevSlide = document.getElementById('btn-prev-slide');
    const btnNextSlide = document.getElementById('btn-next-slide');
    const modalSlideCounter = document.getElementById('modal-slide-counter');

    let currentSlideNodes = [];
    let currentSlideIndex = 0;
    let currentlyHoveredSlideInfo = "";
    
    // LOGIC TOGGLE SIDEBAR
    btnToggleSidebar.addEventListener('click', () => {
        vlearnSidebar.classList.toggle('collapsed');
    });

    // MÔ PHỎNG LUỒNG CHẠY AI
    btnGenerateSummary.addEventListener('click', () => {
        // Tự động ẩn sidebar để tạo không gian rộng rãi cho AI Dashboard
        vlearnSidebar.classList.add('collapsed');
        
        // Ẩn luôn 2 nút Floating khi vào Dashboard
        if (floatingActions) floatingActions.classList.add('hidden');
        
        readingState.classList.remove('active');
        loadingState.classList.add('active');
        
        const loadingText = document.getElementById('loading-text');
        
        setTimeout(() => {
            loadingText.textContent = "Đang trích xuất khái niệm & cấu trúc...";
        }, 1000);

        setTimeout(() => {
            loadingText.textContent = "Đang tạo Flashcard & Mindmap...";
        }, 2000);

        setTimeout(() => {
            loadingState.classList.remove('active');
            afterState.classList.add('active');
        }, 3000);
    });

    // Quay lại màn hình đọc PDF
    btnBackToReading.addEventListener('click', () => {
        afterState.classList.remove('active');
        readingState.classList.add('active');
        
        // Hiện lại 2 nút Floating
        if (floatingActions) floatingActions.classList.remove('hidden');
    });

    // LOGIC LẬT FLASHCARD & TRẮC NGHIỆM
    const demoFlashcard = document.getElementById('demo-flashcard');
    const fcQuestion = document.getElementById('fc-question');
    const fcOptions = document.getElementById('fc-options');
    const fcAnswer = document.getElementById('fc-answer');
    const fcCounter = document.getElementById('fc-counter');
    const btnFcWrong = document.getElementById('btn-fc-wrong');
    const btnFcCorrect = document.getElementById('btn-fc-correct');
    
    const quizData = [
        {
            q: "Nếu AI lọc CV, 'Cost of error' lớn nhất là gì?",
            opts: ["A. Tốn tiền mua API", "B. Loại nhầm ứng viên giỏi (False Negative)", "C. Giao diện khó dùng", "D. Chạy chậm"],
            ans: "B. Loại nhầm ứng viên giỏi (False Negative)"
        },
        {
            q: "Câu hỏi cốt lõi để xác định JTBD (Job) là gì?",
            opts: ["A. Khách hàng muốn tính năng gì?", "B. Khách hàng sẵn sàng trả bao nhiêu?", "C. Khách hàng đang cố hoàn thành việc gì?", "D. Đối thủ đang làm gì?"],
            ans: "C. Khách hàng đang cố hoàn thành việc gì?"
        },
        {
            q: "Tiêu chí nghiệm thu AI nên có yếu tố nào?",
            opts: ["A. Lát cắt 1 câu, có thể đo lường", "B. Viết bằng mã code", "C. Độ dài 10 trang", "D. Chứa thuật toán phức tạp"],
            ans: "A. Lát cắt 1 câu, có thể đo lường"
        },
        {
            q: "'Automate' và 'Augment' khác nhau thế nào?",
            opts: ["A. Automate rẻ hơn", "B. Automate giao toàn quyền, Augment hỗ trợ gợi ý", "C. Không khác biệt", "D. Augment chạy độc lập"],
            ans: "B. Automate giao toàn quyền, Augment hỗ trợ gợi ý"
        },
        {
            q: "'False Positive' (Dương tính giả) nghĩa là gì?",
            opts: ["A. Bỏ sót lỗi", "B. Nhận diện sai một thứ bình thường thành lỗi", "C. Kết quả hoàn hảo", "D. Hệ thống sập"],
            ans: "B. Nhận diện sai một thứ bình thường thành lỗi"
        }
    ];

    let currentCardIdx = 0;
    let quizCompleted = false;

    function renderCard(idx) {
        if(idx >= quizData.length) {
            fcQuestion.innerHTML = "<span class='text-success'><i class='fas fa-trophy'></i> Bạn đã hoàn thành!</span>";
            fcOptions.innerHTML = "<div class='mcq-opt' style='text-align:center;'>Tỉ lệ nhớ: 100%</div>";
            fcAnswer.innerHTML = "Tuyệt vời, bạn đã thuộc hết 5 khái niệm trọng tâm.";
            fcCounter.innerHTML = `<i class="fas fa-layer-group"></i> 5 / 5 Thẻ`;
            quizCompleted = true;
            return;
        }
        const data = quizData[idx];
        fcQuestion.textContent = data.q;
        fcOptions.innerHTML = data.opts.map(opt => `<div class="mcq-opt">${opt}</div>`).join('');
        fcAnswer.textContent = data.ans;
        fcCounter.innerHTML = `<i class="fas fa-layer-group"></i> ${idx + 1} / 5 Thẻ`;
    }

    // Init first card
    if(fcQuestion) renderCard(currentCardIdx);

    if (demoFlashcard) {
        demoFlashcard.addEventListener('click', () => {
            demoFlashcard.classList.toggle('flipped');
        });
    }

    function nextCard() {
        if(quizCompleted) return;
        // Bỏ lật bài nếu đang lật
        if (demoFlashcard.classList.contains('flipped')) {
            demoFlashcard.classList.remove('flipped');
            setTimeout(() => {
                currentCardIdx++;
                renderCard(currentCardIdx);
            }, 300); // Chờ hiệu ứng lật xong mới đổi nội dung
        } else {
            currentCardIdx++;
            renderCard(currentCardIdx);
        }
    }

    if(btnFcWrong) btnFcWrong.addEventListener('click', nextCard);
    if(btnFcCorrect) btnFcCorrect.addEventListener('click', nextCard);

    // LOGIC LỊCH SỬ MODAL
    const btnOpenHistory = document.getElementById('btn-open-history');
    const historyModal = document.getElementById('history-modal');
    const btnCloseHistory = document.getElementById('btn-close-history');

    if(btnOpenHistory && historyModal && btnCloseHistory) {
        btnOpenHistory.addEventListener('click', () => {
            historyModal.classList.remove('hidden');
        });
        btnCloseHistory.addEventListener('click', () => {
            historyModal.classList.add('hidden');
        });
    }

    // MÔ PHỎNG HOVER TRÊN MINDMAP (HIỂN THỊ POPOVER)
    nodes.forEach(node => {
        node.addEventListener('mouseenter', (e) => {
            const slideInfo = node.getAttribute('data-slide');
            popoverSlideNum.textContent = slideInfo;
            currentlyHoveredSlideInfo = slideInfo;
            
            // Lấy kích thước và vị trí của node, kết hợp với scroll của .mindmap-container
            const mindmapContainer = document.querySelector('.mindmap-container');
            const rect = node.getBoundingClientRect();
            const containerRect = mindmapContainer.getBoundingClientRect();
            
            popover.style.display = 'block';
            popover.classList.remove('hidden');
            
            // Căn giữa popover phía trên node
            const popoverWidth = popover.offsetWidth;
            const popoverHeight = popover.offsetHeight;
            
            const topPosition = rect.top - containerRect.top + mindmapContainer.scrollTop - popoverHeight - 10;
            const leftPosition = rect.left - containerRect.left + mindmapContainer.scrollLeft + (rect.width / 2) - (popoverWidth / 2);
            
            popover.style.top = `${topPosition}px`;
            popover.style.left = `${leftPosition}px`;
            popover.style.pointerEvents = 'auto';
        });
    });

    // Ẩn popover khi chuột rời khỏi popover
    popover.addEventListener('mouseleave', () => {
        popover.classList.add('hidden');
        popover.style.pointerEvents = 'none';
        setTimeout(() => {
            if(popover.classList.contains('hidden')) popover.style.display = 'none';
        }, 200);
    });

    if (btnQuickFlashcard) {
        btnQuickFlashcard.addEventListener('click', () => {
            alert(`Đang tạo bộ Flashcard rút gọn dành riêng cho nhánh: ${currentlyHoveredSlideInfo}`);
            popover.classList.add('hidden');
            popover.style.pointerEvents = 'none';
        });
    }

    // LOGIC MODAL SLIDE
    btnViewSlide.addEventListener('click', () => {
        currentSlideNodes = [];
        if (currentlyHoveredSlideInfo.includes('-')) {
            let parts = currentlyHoveredSlideInfo.replace('Slide ', '').split('-');
            let start = parseInt(parts[0]);
            let end = parseInt(parts[1]);
            for(let i = start; i <= end; i++) {
                currentSlideNodes.push(`Slide ${i}`);
            }
        } else if (currentlyHoveredSlideInfo === "Toàn bộ bài") {
            currentSlideNodes = ["Slide 1", "Slide 2", "Slide 3", "Slide 4"]; 
        } else {
            currentSlideNodes = [currentlyHoveredSlideInfo];
        }

        currentSlideIndex = 0;
        updateModalContent();
        
        slideModal.classList.remove('hidden');
        popover.classList.add('hidden');
        popover.style.pointerEvents = 'none';
    });

    btnCloseModal.addEventListener('click', () => {
        slideModal.classList.add('hidden');
    });

    btnNextSlide.addEventListener('click', () => {
        if (currentSlideIndex < currentSlideNodes.length - 1) {
            currentSlideIndex++;
            updateModalContent();
        }
    });

    btnPrevSlide.addEventListener('click', () => {
        if (currentSlideIndex > 0) {
            currentSlideIndex--;
            updateModalContent();
        }
    });

    function updateModalContent() {
        let currentSlide = currentSlideNodes[currentSlideIndex];
        modalSlideTitle.textContent = `Nguồn: ${currentSlide}`;
        
        let pageNumStr = currentSlide.replace('Slide ', '');
        let pageNum = parseInt(pageNumStr);
        if (!isNaN(pageNum)) {
            const pdfIframe = document.getElementById('pdf-iframe');
            if (pdfIframe) {
                pdfIframe.src = `../data/vlearn-pack/slides/d2-slide-hackathon.pdf#page=${pageNum}&toolbar=0&navpanes=0&scrollbar=0`;
            }
        }
        
        modalSlideCounter.textContent = `${currentSlideIndex + 1} / ${currentSlideNodes.length}`;
        
        btnPrevSlide.disabled = (currentSlideIndex === 0);
        btnNextSlide.disabled = (currentSlideIndex === currentSlideNodes.length - 1);
        
        btnPrevSlide.style.opacity = btnPrevSlide.disabled ? '0.3' : '1';
        btnNextSlide.style.opacity = btnNextSlide.disabled ? '0.3' : '1';
    }
});
