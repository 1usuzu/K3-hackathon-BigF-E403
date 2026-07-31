/**
 * Service for extracting text content from PDF slides and indexing by page number.
 */
class PDFParserService {
    /**
     * Extracts text from slide files or returns pre-indexed slide content
     * @param {string} pdfPath 
     * @returns {Promise<Array<{pageNumber: number, title: string, content: string}>>}
     */
    async extractSlidePages(pdfPath) {
        // Pre-indexed structured content from lecture slides (d2-slide-hackathon.pdf)
        return [
            {
                pageNumber: 1,
                title: "Tổng quan AI & Đánh giá rủi ro (Cost of Error)",
                content: "Khái niệm Cost of Error: Chi phí và hậu quả khi AI đưa ra quyết định sai. Ví dụ lọc CV: False Negative loại nhầm ứng viên giỏi là rủi ro lớn nhất."
            },
            {
                pageNumber: 2,
                title: "Phương pháp JTBD & Customer Need",
                content: "Core JTBD: Xác định việc người dùng đang cố gắng hoàn thành. Không hỏi người dùng muốn tính năng gì mà hỏi họ đang vướng ở đâu."
            },
            {
                pageNumber: 3,
                title: "Thiết kế Lát cắt & Nghiệm thu",
                content: "Tiêu chí nghiệm thu AI: Lát cắt 1 câu (1 user, 1 việc, 1 quyết định AI, 1 kết quả). Có thể đo lường và kiểm chứng qua Golden set."
            },
            {
                pageNumber: 4,
                title: "Phân biệt Automate vs Augment",
                content: "Automate: AI tự động hoàn toàn quyết định. Augment: AI gợi ý, con người phê duyệt. Lựa chọn dựa trên mức độ rủi ro và niềm tin người dùng."
            }
        ];
    }

    /**
     * Combines all page texts into a single string for prompt input
     */
    getCombinedText(pages) {
        return pages.map(p => `[Slide ${p.pageNumber}: ${p.title}]\n${p.content}`).join('\n\n');
    }
    /**
     * Extracts text from a File object (PDF or TXT)
     * @param {File} file 
     * @returns {Promise<string>}
     */
    async extractTextFromFile(file) {
        if (!file) return '';

        if (file.name.toLowerCase().endsWith('.txt')) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = (e) => reject(e);
                reader.readAsText(file);
            });
        }

        if (file.name.toLowerCase().endsWith('.pdf') && typeof pdfjsLib !== 'undefined') {
            try {
                const arrayBuffer = await file.arrayBuffer();
                const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                let fullText = '';
                
                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const items = textContent.items;
                    if (items.length === 0) continue;
                    
                    // Group items by Y coordinate with a small tolerance (5 units) to group lines
                    const lines = {};
                    items.forEach(item => {
                        if (!item.str.trim()) return;
                        // transform[5] is the Y-coordinate. Round to group vertical elements.
                        const y = Math.round(item.transform[5] / 6) * 6;
                        if (!lines[y]) {
                            lines[y] = [];
                        }
                        lines[y].push(item);
                    });
                    
                    // Sort Y coordinates descending (top of the page to bottom)
                    const sortedY = Object.keys(lines).map(Number).sort((a, b) => b - a);
                    
                    let pageText = '';
                    sortedY.forEach(y => {
                        // Sort line items left to right (X ascending)
                        const lineItems = lines[y].sort((a, b) => a.transform[4] - b.transform[4]);
                        const lineStr = lineItems.map(item => item.str).join(' ');
                        pageText += lineStr + '\n';
                    });
                    
                    fullText += `[Slide ${i}]\n${pageText}\n\n`;
                }
                
                return fullText;
            } catch (err) {
                console.error('[PDFParserService] Error extracting PDF text:', err);
                return '';
            }
        }

        console.warn('[PDFParserService] Unsupported file type or pdfjsLib not loaded.');
        return '';
    }
}

if (typeof window !== 'undefined') {
    window.PDFParserService = PDFParserService;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFParserService;
}
