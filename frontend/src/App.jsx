import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './index.css';
import ReactECharts from 'echarts-for-react';

axios.defaults.headers.common['ngrok-skip-browser-warning'] = '69420';

// ─── helpers ────────────────────────────────────────────────────────────────
const formatTreeData = (node) => {
  if (!node) return null;
  return {
    name: node.label ? node.label.replace('\n', ' ') : '',
    slide: node.slide,
    children: node.children ? node.children.map(formatTreeData) : [],
  };
};

const COURSE_DATA = [
  { day: 'Day 01', files: ['day01-maianh.pdf'] },
  { day: 'Day 02', files: ['day02-maianh.pdf', 'day02.pdf'] },
  { day: 'Day 03', files: ['day03.pdf'] },
  { day: 'Day 04', files: ['day04-maianh.pdf', 'day04.pdf'] },
  { day: 'Day 05', files: ['day05-maianh.pdf', 'day05.pdf'] },
];

// Loading steps that mirror the 2-step agent pipeline
const LOADING_STEPS = [
  { icon: 'fa-file-alt',    text: 'Đang đọc & phân tích nội dung slide...' },
  { icon: 'fa-sitemap',     text: 'AI đang tạo cấu trúc Mindmap...' },
  { icon: 'fa-clone',       text: 'AI đang tổng hợp Flashcard trắc nghiệm...' },
  { icon: 'fa-check-circle',text: 'Hoàn tất! Chuẩn bị hiển thị...' },
];

// Removed MindmapNode (Vertical tree)

// ─── App ─────────────────────────────────────────────────────────────────────
function App() {
  // app-level state
  const [appState, setAppState] = useState('reading');
  // 'reading' | 'loading' | 'dashboard' | 'quiz' | 'error'
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeDay, setActiveDay]     = useState('Day 01');
  const [selectedPdf, setSelectedPdf] = useState('day01-maianh.pdf');
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);

  useEffect(() => {
    let active = true;
    const loadPdf = async () => {
      try {
        const res = await axios.get(`/pdfs/${selectedPdf}`, { responseType: 'blob' });
        if (active) {
          const url = URL.createObjectURL(res.data);
          setPdfBlobUrl(url);
        }
      } catch (err) {
        console.error('Failed to load PDF blob:', err);
      }
    };
    if (selectedPdf) {
      loadPdf();
    }
    return () => {
      active = false;
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
    };
  }, [selectedPdf]);

  // loading animation
  const [loadingStepIdx, setLoadingStepIdx] = useState(0);

  // agent output
  const [data, setData]       = useState(null);
  const [agentError, setAgentError] = useState(null); // report_error message

  // flashcard state
  const [history, setHistory]           = useState([]); // weak cards (q strings)
  const [currentCardIdx, setCurrentCardIdx] = useState(0);
  const [flipped, setFlipped]           = useState(false);
  const [quizCompleted, setQuizCompleted] = useState(false);

  // quiz state
  const [quizData, setQuizData]           = useState([]);
  const [currentQuizIdx, setCurrentQuizIdx] = useState(0);
  const [quizScore, setQuizScore]         = useState(0);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [quizNoWeakCards, setQuizNoWeakCards] = useState(false);
  const [quizLoading, setQuizLoading] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('flashcards'); // 'flashcards' | 'quiz'

  // mindmap popover
  const mindmapContainerRef = useRef(null);
  const [popoverState, setPopoverState] = useState(
    { visible: false, slide: '', text: '', top: 0, left: 0 }
  );

  // drag to scroll
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [scrollStart, setScrollStart] = useState({ left: 0, top: 0 });

  // slide / history modals
  const [showSlideModal, setShowSlideModal]     = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [modalSlides, setModalSlides]           = useState([]);
  const [modalSlideIdx, setModalSlideIdx]       = useState(0);

  const [generatingSection, setGeneratingSection] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [generatingNodeId, setGeneratingNodeId] = useState(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const runLoadingSteps = () => {
    setLoadingStepIdx(0);
    const timings = [0, 1200, 2600, 4000];
    timings.forEach((t, i) => setTimeout(() => setLoadingStepIdx(i), t));
  };

  // ── generate mindmap + flashcard ────────────────────────────────────────────
  const handleGenerate = async () => {
    setSidebarCollapsed(true);
    setAppState('loading');
    setAgentError(null);
    runLoadingSteps();
    try {
      const res = await axios.post('/api/generate_study_material', {
        student_history: history,
        pdf_filename: selectedPdf,
      });
      if (res.data.status === 'success') {
        setData({ mindmap: res.data.mindmap, flashcards: res.data.flashcards });
        setCurrentCardIdx(0);
        setFlipped(false);
        setQuizCompleted(false);
        setHistory([]);
        setAppState('dashboard');
      } else {
        // agent called report_error → show dedicated error state
        setAgentError(res.data.message);
        setAppState('error');
      }
    } catch {
      setAgentError('Lỗi kết nối tới Server Agent. Vui lòng thử lại.');
      setAppState('error');
    }
  };

  // ── generate quiz ────────────────────────────────────────────────────────────
  const handleGenerateQuiz = async () => {
    if (history.length === 0) return; // chỉ cho phép khi có thẻ yếu
    setQuizNoWeakCards(false);
    setQuizData([]);
    setCurrentQuizIdx(0);
    setQuizScore(0);
    setQuizSubmitted(false);
    setSelectedOption(null);
    setQuizLoading(true);
    setRightPanelTab('quiz');
    try {
      const res = await axios.post('/api/generate_quiz', {
        history,
        pdf_filename: selectedPdf,
      });
      if (res.data.status === 'success') {
        setQuizData(res.data.questions);
      } else {
        setAgentError(res.data.message);
        setAppState('error');
      }
    } catch {
      setAgentError('Lỗi kết nối tới Server Agent. Vui lòng thử lại.');
      setAppState('error');
    } finally {
      setQuizLoading(false);
    }
  };

  // ── section flashcards ───────────────────────────────────────────────────────
  const handleGenerateSectionFlashcards = async (node, nodeId) => {
    if (!node.slide) return;
    setGeneratingNodeId(nodeId);
    const match = node.slide.match(/\d+/g);
    let nodes = [];
    if (match && match.length > 1) {
      for (let i = parseInt(match[0]); i <= parseInt(match[1]); i++) nodes.push(i);
    } else if (match) {
      nodes = [parseInt(match[0])];
    } else {
      nodes = [1];
    }
    try {
      const res = await axios.post('/api/generate_section_flashcards', {
        pdf_filename: selectedPdf, slide_refs: nodes, topic: node.label
      });
      if (res.data.status === 'success') {
        const newCards = res.data.flashcards || [];
        setData(prev => ({ ...prev, flashcards: [...prev.flashcards, ...newCards] }));
      }
    } catch { /* ignore */ }
    finally { setGeneratingNodeId(null); }
  };

  // ── flashcard navigation ─────────────────────────────────────────────────────
  const handleNextCard = (isWrong, qStr) => {
    if (quizCompleted) return;
    if (isWrong) setHistory(prev => [...prev, qStr]);
    const advance = () => {
      if (currentCardIdx < data.flashcards.length - 1) {
        setCurrentCardIdx(c => c + 1);
      } else {
        setQuizCompleted(true);
      }
    };
    if (flipped) {
      setFlipped(false);
      setTimeout(advance, 300);
    } else {
      advance();
    }
  };

  // ── mindmap popover ──────────────────────────────────────────────────────────
  const handleNodeClick = (e, nodeData, nodeId) => {
    e.stopPropagation();
    setSelectedNodeId(nodeId);
    const containerEl = mindmapContainerRef.current;
    if (!containerEl) return;
    const rect = containerEl.getBoundingClientRect();
    setPopoverState({
      visible: true,
      slide: nodeData.slide || '—',
      text: nodeData.label || '',
      top: e.clientY - rect.top + 10,
      left: e.clientX - rect.left + 10,
    });
  };

  const closePopover = () => setPopoverState(p => ({ ...p, visible: false }));

  const renderMindmapNode = (node, isRoot = false) => {
    if (!node) return null;
    const nodeLabel = node.label ? node.label.replace('\n', ' ') : '';
    const nodeSlide = node.slide || '—';
    const nodeId = nodeLabel + nodeSlide;
    const isGenerating = generatingNodeId === nodeId;

    return (
      <li key={nodeId}>
        <div 
          className={`node ${isRoot ? 'root-node' : ''} ${
            (nodeLabel.includes('Phần 1') || nodeLabel.includes('50%')) ? 'status-red' : 
            (nodeLabel.includes('Phần 2') || nodeLabel.includes('Phần 3')) ? 'status-yellow' : 
            'status-gray'
          }`}
          onClick={(e) => handleNodeClick(e, node, nodeId)}
          data-concept={nodeLabel} 
          data-slide={nodeSlide}
        >
          {nodeLabel}
          {!isRoot && (
            <button 
              className="node-flashcard-btn" 
              title="Tạo Flashcard cho nhánh này"
              disabled={isGenerating}
              onClick={(e) => {
                e.stopPropagation();
                handleGenerateSectionFlashcards(node, nodeId);
              }}
            >
              {isGenerating ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-bolt"></i>}
            </button>
          )}
        </div>
        {node.children && node.children.length > 0 && (
          <ul>
            {node.children.map((child, idx) => (
              <React.Fragment key={idx}>
                {renderMindmapNode(child, false)}
              </React.Fragment>
            ))}
          </ul>
        )}
      </li>
    );
  };

  const handleWheel = (e) => {
    if (e.ctrlKey || e.metaKey) {
      setZoom(z => Math.min(Math.max(0.2, z - e.deltaY * 0.002), 3));
    } else {
      setPan(p => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    }
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.pageX - pan.x, y: e.pageY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({ x: e.pageX - dragStart.x, y: e.pageY - dragStart.y });
  };

  const handleMouseUpOrLeave = () => {
    setIsDragging(false);
  };

  const handleViewSlide = () => {
    const si = popoverState.slide;
    let nodes = [];
    if (si === 'Toàn bộ bài') {
      nodes = [1];
    } else if (si) {
      const parts = si.split(',');
      parts.forEach(part => {
        const p = part.trim();
        if (p.includes('-')) {
          const [start, end] = p.split('-');
          const s = parseInt(start), e = parseInt(end);
          if (!isNaN(s) && !isNaN(e)) {
            for (let i = s; i <= e; i++) nodes.push(i);
          }
        } else {
          const val = parseInt(p);
          if (!isNaN(val)) nodes.push(val);
        }
      });
    }
    if (nodes.length === 0) nodes = [1];
    setModalSlides([...new Set(nodes)]); // remove duplicates
    setModalSlideIdx(0);
    setShowSlideModal(true);
    closePopover();
  };

  // ── derived values ───────────────────────────────────────────────────────────
  const currentStep  = LOADING_STEPS[loadingStepIdx] || LOADING_STEPS[0];
  const card         = data?.flashcards?.[currentCardIdx];
  const weakCount    = history.length;
  const totalCards   = data?.flashcards?.length ?? 0;
  const progressPct  = totalCards > 0 ? Math.round((currentCardIdx / totalCards) * 100) : 0;
  const masteredCount = currentCardIdx - weakCount; // approximation for display

  return (
    <>
      {/* ── HEADER ─────────────────────────────────────────────────────── */}
      <header className="vlearn-header">
        <div className="header-left">
          <button className="icon-btn btn-back"><i className="fas fa-chevron-left"></i></button>
          <div className="logo">
            <i className="fab fa-vuejs" style={{color:'#e11d48',fontSize:'20px'}}></i>
            <span style={{fontWeight:700,color:'#1e293b',fontSize:'18px',marginLeft:'4px'}}>VLearn</span>
          </div>
          <div className="header-divider"></div>
          <div className="document-info">
            <i className="far fa-file-pdf" style={{color:'#64748b',fontSize:'18px'}}></i>
            <div className="doc-text">
              <div className="doc-title">{selectedPdf}
                <i className="fas fa-check-circle" style={{color:'#2563eb',fontSize:'12px',marginLeft:'4px'}}></i>
              </div>
              <div className="doc-subtitle">COMP2010 · Lecture_material_ms2039d0_hnxpxy</div>
            </div>
          </div>
        </div>
        <div className="header-right">
          <div className="status-badge"><i className="fas fa-check"></i> Ghi chú đã lưu</div>
          <button className="lang-btn">VI</button>
          <button className="icon-btn theme-toggle"><i className="far fa-moon"></i></button>
        </div>
      </header>

      <div className="vlearn-layout">
        {/* ── SIDEBAR ──────────────────────────────────────────────────── */}
        <aside className={`vlearn-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="sidebar-header">
            <div className="sidebar-icon-wrap"><i className="fas fa-book-open"></i></div>
            <div className="sidebar-title">
              <h4>Học liệu môn học</h4>
              <p>Chương, slide và tài liệu đã upload</p>
            </div>
          </div>
          <div className="sidebar-content">
            {COURSE_DATA.map((course, idx) => (
              <div key={idx} className={`accordion-item ${activeDay === course.day ? 'active' : ''}`}>
                <div className="accordion-header" onClick={() => setActiveDay(activeDay === course.day ? '' : course.day)}>
                  <i className="far fa-play-circle" style={{color: activeDay === course.day ? '#2563eb' : '#64748b', fontSize:'18px'}}></i>
                  <div className="acc-text">
                    <strong>{course.day}</strong>
                    <p>{course.files.length} TÀI LIỆU</p>
                  </div>
                  {activeDay === course.day && <span className="badge-studying">STUDYING</span>}
                  <i className={`fas ${activeDay === course.day ? 'fa-chevron-up' : 'fa-chevron-down'} acc-icon`}></i>
                </div>
                {activeDay === course.day && (
                  <div className="accordion-body">
                    {course.files.map((file, fIdx) => (
                      <div key={fIdx}
                        className={`doc-item ${selectedPdf === file ? 'active' : ''}`}
                        style={{cursor:'pointer'}}
                        onClick={() => { 
                          if (selectedPdf !== file) {
                            setData(null);
                            setHistory([]);
                            setQuizData(null);
                          }
                          setSelectedPdf(file); 
                          setAppState('reading'); 
                          setAgentError(null); 
                        }}>
                        <i className="far fa-play-circle"></i>
                        <div className="doc-item-text"><strong>{file}</strong></div>
                        {selectedPdf === file && <i className="far fa-check-circle" style={{color:'#2563eb'}}></i>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </aside>

        <button className="sidebar-toggle-btn" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
          <i className="fas fa-chevron-left"></i>
        </button>

        {/* ── MAIN ─────────────────────────────────────────────────────── */}
        <main className="vlearn-main">

          {/* STATE: READING */}
          <div className={`state-container ${appState === 'reading' ? 'active' : ''}`}>
            <div className="pdf-toolbar-container">
              <div className="pdf-toolbar">
                <div className="toolbar-group">
                  <button className="tool-btn active"><i className="fas fa-mouse-pointer"></i> Đọc</button>
                  <button className="tool-btn"><i className="fas fa-pen"></i> Bút</button>
                  <button className="tool-btn"><i className="fas fa-highlighter"></i> Highlight</button>
                </div>
                <div className="toolbar-divider"></div>
                <div className="toolbar-group"><span className="page-info">Trang 1 • 1 note</span></div>
                <div className="toolbar-divider"></div>
                <div className="toolbar-group">
                  <button className="tool-btn icon-only"><i className="fas fa-minus"></i></button>
                  <span className="zoom-level">100%</span>
                  <button className="tool-btn icon-only"><i className="fas fa-plus"></i></button>
                </div>
              </div>
            </div>
            <div className="pdf-viewer-area">
              <div className="pdf-page-container">
                {pdfBlobUrl ? (
                  <iframe src={`${pdfBlobUrl}#page=1`}
                    width="100%" height="100%" frameBorder="0"></iframe>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                    <div className="spinner"></div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* STATE: LOADING */}
          <div className={`state-container ${appState === 'loading' ? 'active' : ''}`}
            style={{justifyContent:'center',alignItems:'center',background:'rgba(255,255,255,0.92)'}}>
            <div className="loading-content">
              <div className="ai-pipeline-badge">
                <i className="fas fa-robot"></i> VLearn AI Agent đang xử lý
              </div>
              <div className="spinner" style={{margin:'24px auto 0'}}></div>
              <h3 className="loading-step-text">
                <i className={`fas ${currentStep.icon}`}></i> {currentStep.text}
              </h3>
              <div className="pipeline-steps">
                {LOADING_STEPS.map((step, i) => (
                  <div key={i} className={`pipeline-step ${i <= loadingStepIdx ? 'done' : ''} ${i === loadingStepIdx ? 'active' : ''}`}>
                    <div className="step-dot"></div>
                    <span>{step.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* STATE: ERROR (agent called report_error) */}
          <div className={`state-container ${appState === 'error' ? 'active' : ''}`}
            style={{justifyContent:'center',alignItems:'center'}}>
            <div className="agent-error-card">
              <div className="agent-error-icon"><i className="fas fa-shield-alt"></i></div>
              <h3>AI không thể xử lý nội dung này</h3>
              <p className="agent-error-msg">{agentError}</p>
              <div className="agent-error-why">
                <strong><i className="fas fa-info-circle"></i> Tại sao?</strong>
                <p>Agent được thiết kế để <em>không bịa đặt kiến thức</em>. Khi slide không có đủ nội dung học thuật hợp lệ, agent sẽ từ chối thay vì tạo ra Mindmap / Flashcard sai.</p>
              </div>
              <div style={{display:'flex',gap:'12px',marginTop:'24px'}}>
                <button className="btn-primary" onClick={() => { setAppState('reading'); setAgentError(null); }}>
                  <i className="fas fa-arrow-left"></i> Chọn slide khác
                </button>
                {data && (
                  <button className="btn-outline" onClick={() => setAppState('dashboard')}>
                    <i className="fas fa-th-large"></i> Xem kết quả cũ
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* STATE: DASHBOARD */}
          <div className={`state-container ${appState === 'dashboard' ? 'active' : ''}`}>
            {/* dashboard header with live agent stats */}
            <div className="dashboard-header">
              <div>
                <h2>TỔNG KẾT &amp; ÔN TẬP <span className="ai-tag">AI-POWERED</span></h2>
                <div className="agent-stats-row">
                  <span className="stat-chip stat-mindmap"><i className="fas fa-sitemap"></i> Mindmap đã tạo</span>
                  <span className="stat-chip stat-flashcard"><i className="fas fa-clone"></i> {totalCards} Flashcards</span>
                  {weakCount > 0 && (
                    <span className="stat-chip stat-weak"><i className="fas fa-exclamation-triangle"></i> {weakCount} thẻ yếu</span>
                  )}
                  {weakCount === 0 && currentCardIdx > 0 && (
                    <span className="stat-chip stat-ok"><i className="fas fa-check-circle"></i> Không có thẻ yếu</span>
                  )}
                </div>
              </div>
              <button className="btn-sm btn-outline" onClick={() => setAppState('reading')}>
                <i className="fas fa-arrow-left"></i> Trở về bài giảng
              </button>
            </div>

            {data && (
              <div className="dashboard-grid">
                {/* ── LEFT: MINDMAP ─────────────────────────────────────── */}
                <div className="left-column">
                  <div className="panel">
                    <div className="panel-header">
                      <h3><i className="fas fa-sitemap"></i> Mindmap Bài giảng</h3>
                      <div style={{display:'flex', gap:'12px', fontSize:'11px', fontWeight:600, marginLeft:'auto', marginRight:'16px'}}>
                        <span style={{color: '#94a3b8'}}><span style={{display:'inline-block', width:8, height:8, borderRadius:'50%', background:'#e2e8f0', marginRight:4}}></span>Chưa học</span>
                        <span style={{color: '#d97706'}}><span style={{display:'inline-block', width:8, height:8, borderRadius:'50%', background:'#fbbf24', marginRight:4}}></span>Đã xem thẻ</span>
                        <span style={{color: '#15803d'}}><span style={{display:'inline-block', width:8, height:8, borderRadius:'50%', background:'#10b981', marginRight:4}}></span>Đã thuộc</span>
                        <span style={{color: '#b91c1c'}}><span style={{display:'inline-block', width:8, height:8, borderRadius:'50%', background:'#ef4444', marginRight:4}}></span>Cần ôn lại</span>
                      </div>
                      <div style={{display:'flex',gap:'8px',alignItems:'center'}}>
                        <span className="agent-method-badge"><i className="fas fa-robot"></i> generate_mindmap</span>
                        <button className="icon-btn"><i className="fas fa-expand"></i></button>
                      </div>
                    </div>
                    <div 
                      className="panel-body mindmap-container" 
                      ref={mindmapContainerRef} 
                      style={{position:'relative'}}
                      onWheel={handleWheel}
                      onMouseDown={handleMouseDown}
                      onMouseMove={handleMouseMove}
                      onMouseUp={handleMouseUpOrLeave}
                      onMouseLeave={handleMouseUpOrLeave}
                    >
                      <div className="tree-wrapper" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}>
                        <div className="tree">
                          <ul>
                            {renderMindmapNode(data.mindmap, true)}
                          </ul>
                        </div>
                      </div>
                      
                      {/* Popover */}
                      {popoverState.visible && (
                        <div className="popover"
                          style={{top:popoverState.top,left:popoverState.left}}
                          onMouseLeave={closePopover}>
                          <div className="popover-content">
                            <div className="popover-top">
                              <span className="slide-ref"><i className="fas fa-file-pdf"></i> Nguồn: <strong>{popoverState.slide}</strong></span>
                            </div>
                            <div className="popover-actions mt-8">
                              <button className="btn-sm btn-secondary" onClick={handleViewSlide}>
                                <i className="fas fa-eye"></i> Xem Slide
                              </button>
                            </div>
                          </div>
                          <div className="popover-arrow"></div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* ── RIGHT: FLASHCARD + HISTORY ────────────────────────── */}
                <div className="right-column">
                  <div className="panel flashcard-panel">
                    <div className="tab-switcher">
                      <button className={`tab-btn ${rightPanelTab === 'flashcards' ? 'active' : ''}`} onClick={() => setRightPanelTab('flashcards')}>
                        <i className="fas fa-clone"></i> Flashcards
                      </button>
                      <button className={`tab-btn ${rightPanelTab === 'quiz' ? 'active' : ''}`} onClick={() => setRightPanelTab('quiz')}>
                        <i className="fas fa-clipboard-question"></i> Take Quiz
                      </button>
                    </div>

                    {rightPanelTab === 'flashcards' && (
                    <div className="panel-body" style={{display:'flex',flexDirection:'column'}}>
                      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px'}}>
                        <span className="agent-method-badge"><i className="fas fa-robot"></i> generate_flashcards</span>
                        {totalCards > 0 && !quizCompleted && (
                          <div className="fc-progress-wrap" title={`${progressPct}% hoàn thành`} style={{width:'80px'}}>
                            <div className="fc-progress-bar" style={{width:`${progressPct}%`}}></div>
                          </div>
                        )}
                      </div>

                      {/* ── Active flashcard ──────────────────────────── */}
                      {!quizCompleted && card ? (
                        <>
                          <div className="flashcard-interactive">
                            <div className="flip-card" onClick={() => setFlipped(f => !f)}>
                              <div className={`flip-card-inner ${flipped ? 'flipped' : ''}`}>
                                {/* Front */}
                                <div className="flip-card-front">
                                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                                    <span className="card-tag" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                                      <i className="fas fa-code-branch"></i> Nhánh: {card.topic || 'Toàn bài giảng'}
                                    </span>
                                    {card.personalized && (
                                      <span className="card-tag card-tag-weak">
                                        <i className="fas fa-redo"></i> HỌC LẠI
                                      </span>
                                    )}
                                  </div>
                                  <h4>{card.q}</h4>
                                  <div className="mcq-options">
                                    {card.opts?.map((opt, i) => (
                                      <div key={i} className="mcq-opt">{opt}</div>
                                    ))}
                                  </div>
                                  <p className="click-hint"><i className="fas fa-hand-pointer"></i> Nhấp vào thẻ để xem đáp án</p>
                                </div>
                                {/* Back */}
                                <div className="flip-card-back">
                                  <div className="answer-content">
                                    <h4><i className="fas fa-check-circle"></i> Đáp án:</h4>
                                    <p>{card.ans}</p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="flashcard-actions">
                            {/* top row: counter + mark buttons */}
                            <div className="flashcard-actions-top">
                              <div className="flashcard-stats">
                                <i className="fas fa-layer-group"></i> {currentCardIdx + 1} / {totalCards}
                                {weakCount > 0 && (
                                  <span className="weak-badge">
                                    <i className="fas fa-exclamation-circle"></i> {weakCount} yếu
                                  </span>
                                )}
                              </div>
                              <div className="fc-mark-btns">
                                <button className="fc-mark-btn fc-mark-wrong" title="Chưa thuộc"
                                  onClick={(e) => { e.stopPropagation(); handleNextCard(true, card.q); }}>
                                  <i className="fas fa-times"></i>
                                </button>
                                <button className="fc-mark-btn fc-mark-correct" title="Đã thuộc"
                                  onClick={(e) => { e.stopPropagation(); handleNextCard(false, card.q); }}>
                                  <i className="fas fa-check"></i>
                                </button>
                              </div>
                            </div>
                            {/* bottom row: quiz button — only when there are weak cards */}
                            {weakCount > 0 && (
                              <button className="quiz-trigger-btn full-width" onClick={handleGenerateQuiz}>
                                <i className="fas fa-bolt"></i> Tạo Quiz từ {weakCount} thẻ yếu
                              </button>
                            )}
                          </div>
                        </>
                      ) : (

                        /* ── Completion screen ──────────────────────── */
                        <div className="flashcard-completion">
                          <div className="completion-hero">
                            <i className="fas fa-check-circle" style={{color:'#10b981',fontSize:'48px'}}></i>
                            <h3>Đã ôn tập xong {totalCards} thẻ!</h3>
                          </div>

                          {/* Summary chips */}
                          <div className="completion-chips">
                            <div className="chip chip-green">
                              <i className="fas fa-check"></i>
                              <span><strong>{totalCards - weakCount}</strong> Đã thuộc</span>
                            </div>
                            <div className={`chip ${weakCount > 0 ? 'chip-red' : 'chip-green'}`}>
                              <i className={weakCount > 0 ? 'fas fa-exclamation-circle' : 'fas fa-check'}></i>
                              <span><strong>{weakCount}</strong> Thẻ yếu</span>
                            </div>
                          </div>

                          {/* Next steps */}
                          <div className="next-steps">
                            {/* Quiz option — only when there are weak cards */}
                            {weakCount > 0 && (
                              <div className="next-step-card" onClick={handleGenerateQuiz}>
                                <div className="next-step-icon" style={{background:'#38bdf8'}}>
                                  <i className="fas fa-star" style={{color:'white'}}></i>
                                </div>
                                <div style={{flex:1}}>
                                  <strong>Tạo Mini-Quiz từ thẻ yếu</strong>
                                  <p>AI sẽ sinh Quiz kiểm tra lại <b>{weakCount}</b> khái niệm bạn chưa nắm.</p>
                                  <span className="agent-method-badge small"><i className="fas fa-robot"></i> generate_quiz</span>
                                </div>
                                <i className="fas fa-chevron-right" style={{color:'#64748b',alignSelf:'center'}}></i>
                              </div>
                            )}

                            <div className="next-step-card"
                              onClick={() => { setCurrentCardIdx(0); setQuizCompleted(false); setFlipped(false); setHistory([]); }}>
                              <div className="next-step-icon" style={{background:'#3b82f6'}}>
                                <i className="fas fa-layer-group" style={{color:'white'}}></i>
                              </div>
                              <div style={{flex:1}}>
                                <strong>Đặt lại Thẻ ghi nhớ</strong>
                                <p>Học lại tất cả {totalCards} thẻ từ đầu.</p>
                              </div>
                              <i className="fas fa-chevron-right" style={{color:'#64748b',alignSelf:'center'}}></i>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    )}

                    {rightPanelTab === 'quiz' && (
                      <div className="panel-body" style={{display:'flex',flexDirection:'column'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px'}}>
                          <span className="agent-method-badge"><i className="fas fa-robot"></i> generate_quiz</span>
                        </div>
                        {quizNoWeakCards && (
                          <div style={{textAlign:'center', marginTop:'40px'}}>
                            <div className="agent-error-icon" style={{background:'#ecfdf5',color:'#10b981',margin:'0 auto 16px',width:'48px',height:'48px',fontSize:'24px'}}>
                              <i className="fas fa-check-circle"></i>
                            </div>
                            <h3 style={{color:'#047857'}}>Bạn đã nắm vững!</h3>
                            <p style={{color:'#64748b',fontSize:'13px',marginTop:'8px'}}>Không có thẻ yếu nên AI không tạo Quiz.</p>
                          </div>
                        )}
                        {!quizNoWeakCards && quizData.length === 0 && !quizLoading && (
                          <div style={{textAlign:'center', marginTop:'40px', padding:'0 16px'}}>
                            <i className="fas fa-clipboard-question" style={{fontSize:'48px',color:'#cbd5e1',marginBottom:'16px', display:'block'}}></i>
                            <p style={{color:'#64748b',fontSize:'14px',lineHeight:'1.6'}}>
                              Đánh dấu thẻ <strong>chưa thuộc</strong> ở tab Flashcards<br/>để mở khoá Quiz ôn tập.
                            </p>
                          </div>
                        )}
                        {quizLoading && (
                          <div style={{textAlign:'center', marginTop:'40px'}}>
                            <div className="spinner" style={{margin:'0 auto 16px'}}></div>
                            <p style={{color:'#64748b',fontSize:'13px'}}>AI đang tạo Quiz từ thẻ yếu...</p>
                          </div>
                        )}
                        {!quizNoWeakCards && quizData.length > 0 && currentQuizIdx < quizData.length && (
                          <div className="quiz-container" style={{padding:0, margin:0, width:'100%'}}>
                            <div className="quiz-progress-bar-wrap" style={{marginBottom:'16px'}}>
                              <div className="quiz-progress-bar" style={{width:`${((currentQuizIdx)/quizData.length)*100}%`}}></div>
                            </div>
                            <div style={{marginBottom:'12px',color:'#64748b',fontWeight:'bold',fontSize:'12px'}}>
                              Câu {currentQuizIdx + 1} / {quizData.length}
                            </div>
                            <h3 className="quiz-question" style={{fontSize:'16px',marginBottom:'20px'}}>{quizData[currentQuizIdx].question_text}</h3>
                            <div className="quiz-options">
                              {quizData[currentQuizIdx].options.map((opt, i) => {
                                let cls = 'quiz-opt';
                                if (quizSubmitted) {
                                  if (opt === quizData[currentQuizIdx].correct_answer) cls += ' correct';
                                  else if (selectedOption === opt) cls += ' wrong';
                                } else if (selectedOption === opt) {
                                  cls += ' selected';
                                }
                                return (
                                  <div key={i} className={cls} style={{padding:'10px 14px',fontSize:'13px'}}
                                    onClick={() => !quizSubmitted && setSelectedOption(opt)}>
                                    <span className="opt-letter" style={{width:'24px',height:'24px',fontSize:'11px'}}>{String.fromCharCode(65+i)}</span>
                                    {opt}
                                  </div>
                                );
                              })}
                            </div>
                            {quizSubmitted && (
                              <div className="quiz-explanation" style={{marginTop:'16px',padding:'12px 16px'}}>
                                <h4 style={{fontSize:'13px'}}><i className="fas fa-info-circle"></i> Giải thích:</h4>
                                <p style={{fontSize:'12px'}}>{quizData[currentQuizIdx].explanation}</p>
                              </div>
                            )}
                            <div className="quiz-footer" style={{marginTop:'24px', display:'flex'}}>
                              {!quizSubmitted ? (
                                <button className="btn-primary full-width" disabled={!selectedOption} style={{flex: 1}}
                                  onClick={() => {
                                    setQuizSubmitted(true);
                                    if (selectedOption === quizData[currentQuizIdx].correct_answer)
                                      setQuizScore(s => s + 1);
                                  }}>Xác nhận</button>
                              ) : (
                                <button className="btn-primary full-width" style={{flex: 1}}
                                  onClick={() => {
                                    if (currentQuizIdx < quizData.length - 1) {
                                      setCurrentQuizIdx(c => c + 1);
                                      setSelectedOption(null);
                                      setQuizSubmitted(false);
                                    } else {
                                      setCurrentQuizIdx(quizData.length); // go to result
                                    }
                                  }}>
                                  {currentQuizIdx < quizData.length - 1 ? 'Câu tiếp theo' : 'Xem kết quả'}
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                        {!quizNoWeakCards && quizData.length > 0 && currentQuizIdx >= quizData.length && (
                          <div className="quiz-result" style={{padding:'24px 0'}}>
                            <i className="fas fa-award" style={{fontSize:'64px',color:'#f59e0b',marginBottom:'16px'}}></i>
                            <h2 style={{fontSize:'20px'}}>Hoàn thành!</h2>
                            <p style={{fontSize:'14px'}}>Đạt: <strong style={{color:'#10b981',fontSize:'20px'}}>{quizScore} / {quizData.length}</strong></p>
                            <button className="btn-primary" style={{marginTop:'24px'}} onClick={() => { setQuizData([]); setRightPanelTab('flashcards'); }}>
                              <i className="fas fa-arrow-left"></i> Ôn tập lại
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* History mini-panel */}
                  <div className="panel history-mini-panel" style={{cursor:'pointer'}} onClick={() => setShowHistoryModal(true)}>
                    <div className="panel-body" style={{padding:'12px 16px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                      <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                        <i className="fas fa-history" style={{color:'var(--vl-primary)'}}></i>
                        <strong style={{fontSize:'13px'}}>Lịch sử học</strong>
                        {weakCount > 0 && <span className="weak-badge"><i className="fas fa-exclamation-circle"></i> {weakCount}</span>}
                      </div>
                      <div style={{fontSize:'12px',color:'var(--vl-text-sub)',display:'flex',alignItems:'center',gap:'8px'}}>
                        {activeDay} · {selectedPdf} <i className="fas fa-chevron-right"></i>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>



        </main>

        {/* Floating action button — only in reading state */}
        <div className={`floating-actions ${appState !== 'reading' ? 'hidden' : ''}`}>
          <button className="fab-btn vlearn-ai-btn" title="Chat với VLearn AI">
            <i className="fas fa-robot"></i>
          </button>
          <button className="fab-btn auto-summary-btn" title="Tạo Tổng kết & Ôn tập (AI)" onClick={handleGenerate}>
            <i className="fas fa-magic"></i>
          </button>
        </div>
      </div>

      {/* ── SLIDE MODAL ───────────────────────────────────────────────── */}
      <div className={`modal-overlay ${showSlideModal ? '' : 'hidden'}`}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>Nguồn: Trang {popoverState.slide}</h3>
            <button className="icon-btn" onClick={() => setShowSlideModal(false)}><i className="fas fa-times"></i></button>
          </div>
          <div className="modal-body">
            <div className="slide-viewer-mock">
              <div className="mock-slide-image">
                {modalSlides.length > 0 && (
                  <iframe
                    key={`${selectedPdf}-${modalSlides[modalSlideIdx]}`}
                    src={`/pdfs/${selectedPdf}#page=${modalSlides[modalSlideIdx]}`}
                    width="100%" height="100%" frameBorder="0"></iframe>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── HISTORY MODAL ─────────────────────────────────────────────── */}
      <div className={`modal-overlay ${showHistoryModal ? '' : 'hidden'}`}>
        <div className="modal-content" style={{maxWidth:'600px',height:'auto',maxHeight:'80vh'}}>
          <div className="modal-header">
            <h3><i className="fas fa-chart-line"></i> Lịch sử học tập</h3>
            <button className="icon-btn" onClick={() => setShowHistoryModal(false)}><i className="fas fa-times"></i></button>
          </div>
          <div className="modal-body" style={{padding:0,overflowY:'auto'}}>
            <table className="history-table">
              <thead>
                <tr><th>Ngày học</th><th>Nội dung</th><th>Hoàn thành</th></tr>
              </thead>
              <tbody>
                <tr className="active-row">
                  <td>Hôm nay</td>
                  <td>{activeDay}: {selectedPdf}</td>
                  <td>
                    {quizCompleted
                      ? <><strong>100%</strong> <i className="fas fa-check-circle text-success"></i></>
                      : <span className="badge-status">Đang học ({progressPct}%)</span>}
                  </td>
                </tr>
                {history.length > 0 && (
                  <tr>
                    <td colSpan="3" style={{background:'#fef2f2',padding:'16px'}}>
                      <strong style={{color:'#ef4444',fontSize:'14px'}}>
                        <i className="fas fa-exclamation-triangle"></i> Thẻ chưa thuộc ({history.length}):
                      </strong>
                      <ul style={{marginTop:'12px',paddingLeft:'24px',color:'#64748b',fontSize:'13px',lineHeight:'1.6'}}>
                        {history.map((q, i) => <li key={i}>{q}</li>)}
                      </ul>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
