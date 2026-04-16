"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  History,
  Target,
  Code,
  TrendingUp,
  Sparkles,
  Send,
  Settings,
  User,
  Brain,
  Zap,
  MessageCircle,
  X,
  BookOpen,
  ShoppingBag,
  Video,
  Activity,
  Wand2,
  MonitorPlay,
} from "lucide-react";

const quickTemplates = [
  {
    id: 1,
    title: "爆款产品发布",
    description: "生成极具煽动性的新品发布会全套话术与演示大纲",
    icon: Target,
  },
  {
    id: 2,
    title: "纯代码实战教学",
    description: "提取核心代码片段，生成技术主播的硬核讲解剧本",
    icon: Code,
  },
  {
    id: 3,
    title: "行业趋势分析",
    description: "聚合最新研报，生成高维度的商业洞察直播大纲",
    icon: TrendingUp,
  },
];

const recentSessions = [
  "React 19 核心特性解析",
  "AI Agent 架构实战",
  "SaaS 商业模式拆解",
];

interface ActionQueueItem {
  type: string;
  content?: string;
  scene?: string;
}

interface LiveData {
  success: boolean;
  topic: string;
  director_outline: string;
  anchor_output: string;
  raw_script: string;
  action_queue: ActionQueueItem[];
  obs_commands: any[];
}

interface BusinessAssets {
  success: boolean;
  course_material: string;
  xiaohongshu: string;
  douyin: string;
}

interface JudgeReport {
  success: boolean;
  full_report: string;
  radar_scores?: {
    geek_score: number;
    interaction_score: number;
    commerce_score: number;
  };
}

interface TutorMessage {
  role: "user" | "assistant";
  content: string;
}

export default function HomePage() {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [liveData, setLiveData] = useState<LiveData | null>(null);

  const [businessAssets, setBusinessAssets] = useState<BusinessAssets | null>(null);
  const [isGeneratingAssets, setIsGeneratingAssets] = useState(false);

  const [judgeReport, setJudgeReport] = useState<JudgeReport | null>(null);
  const [isGeneratingJudge, setIsGeneratingJudge] = useState(false);

  const [tutorMessages, setTutorMessages] = useState<TutorMessage[]>([]);
  const [isTutorTyping, setIsTutorTyping] = useState(false);
  const [isTutorOpen, setIsTutorOpen] = useState(false);
  const [tutorInput, setTutorInput] = useState("");

  const [isTeleprompterOpen, setIsTeleprompterOpen] = useState(false);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const teleprompterRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [tutorMessages, isTutorTyping]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isTeleprompterOpen) return;

      e.preventDefault();

      if (e.key === " " || e.key === "ArrowDown") {
        setCurrentLineIndex((prev) => 
          liveData ? Math.min(prev + 1, liveData.action_queue.length - 1) : prev
        );
      } else if (e.key === "ArrowUp") {
        setCurrentLineIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Escape") {
        setIsTeleprompterOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isTeleprompterOpen, liveData]);

  useEffect(() => {
    if (isTeleprompterOpen && teleprompterRef.current) {
      const lineElements = teleprompterRef.current.querySelectorAll("[data-line-index]");
      const currentLine = lineElements[currentLineIndex] as HTMLElement;
      if (currentLine) {
        currentLine.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [currentLineIndex, isTeleprompterOpen]);

  const handleTemplateClick = (title: string) => {
    setInputValue(title);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    setIsLoading(true);
    setLiveData(null);
    setBusinessAssets(null);
    setJudgeReport(null);
    setTutorMessages([]);

    try {
      const response = await fetch("http://localhost:8000/api/v1/live/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ topic: inputValue }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLiveData(data);
    } catch (error) {
      console.error("API 请求失败:", error);
      alert("请求失败，请检查后端服务是否正常运行");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAssets = async () => {
    if (!liveData) return;

    setIsGeneratingAssets(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/business/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action_queue: liveData.action_queue }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setBusinessAssets(data);
    } catch (error) {
      console.error("商业资产生成失败:", error);
      alert("商业资产生成失败，请检查后端服务");
    } finally {
      setIsGeneratingAssets(false);
    }
  };

  const handleGenerateJudge = async () => {
    if (!liveData) return;

    setIsGeneratingJudge(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/judge/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action_queue: liveData.action_queue,
          danmu_history: "",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setJudgeReport(data);
    } catch (error) {
      console.error("复盘报告生成失败:", error);
      alert("复盘报告生成失败，请检查后端服务");
    } finally {
      setIsGeneratingJudge(false);
    }
  };

  const handleTutorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tutorInput.trim() || !businessAssets) return;

    const newMessage: TutorMessage = {
      role: "user",
      content: tutorInput,
    };

    setTutorMessages((prev) => [...prev, newMessage]);
    setTutorInput("");
    setIsTutorTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/tutor/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_question: tutorInput,
          course_material: businessAssets.course_material,
          chat_history: tutorMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTutorMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (error) {
      console.error("助教对话失败:", error);
      setTutorMessages((prev) => [
        ...prev,
        { role: "assistant", content: "抱歉，出现了一些问题，请稍后再试。" },
      ]);
    } finally {
      setIsTutorTyping(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  const radarData = judgeReport?.radar_scores
    ? [
        { subject: "极客硬核度", A: judgeReport.radar_scores.geek_score, fullMark: 100 },
        { subject: "互动引导率", A: judgeReport.radar_scores.interaction_score, fullMark: 100 },
        { subject: "商业转化埋点", A: judgeReport.radar_scores.commerce_score, fullMark: 100 },
      ]
    : [
        { subject: "极客硬核度", A: 0, fullMark: 100 },
        { subject: "互动引导率", A: 0, fullMark: 100 },
        { subject: "商业转化埋点", A: 0, fullMark: 100 },
      ];

  return (
    <div className="min-h-screen bg-[#050505] flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-[260px] border-r border-white/10 flex flex-col bg-[#050505]">
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-400 flex items-center justify-center">
                <div className="w-5 h-5 text-white font-bold">
                  <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
                    <path
                      d="M4 12C4 7.58172 7.58172 4 12 4C16.4183 4 20 7.58172 20 12C20 16.4183 16.4183 20 12 20"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <path
                      d="M12 8V12L15 14"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-cyan-400 border-2 border-[#050505] animate-pulse" />
            </div>
            <span className="text-gray-300 font-semibold text-lg">DeepInsight</span>
          </div>
        </div>

        {/* Recent Sessions */}
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-2">
            Recent Sessions
          </h3>
          <div className="space-y-1">
            {recentSessions.map((session, index) => (
              <button
                key={index}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left group hover:bg-white/5 transition-colors"
              >
                <History className="w-4 h-4 text-gray-500 group-hover:text-gray-300" />
                <span className="text-gray-400 text-sm group-hover:text-white transition-colors">
                  {session}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center border border-white/10">
                <User className="w-4 h-4 text-gray-400" />
              </div>
              <span className="text-gray-300 text-sm font-medium">Admin</span>
            </div>
            <button className="p-2 rounded-lg hover:bg-white/5 transition-colors">
              <Settings className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 flex flex-col px-8 pb-32 pt-8">
          {/* 状态 A: 初始状态 */}
          {!isLoading && !liveData && (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="flex-1 flex flex-col items-center justify-center"
            >
              {/* Hero Text */}
              <motion.div variants={itemVariants} className="text-center mb-12">
                <h1 className="text-5xl md:text-6xl font-bold mb-4">
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-500 via-purple-400 to-cyan-400">
                    DeepInsight / 你的全自动直播内容工厂
                  </span>
                </h1>
                <p className="text-gray-400 text-lg">
                  输入主题，一键生成多智能体直播剧本与全套商业变现资产。
                </p>
              </motion.div>

              {/* Quick Start Cards */}
              <motion.div
                variants={itemVariants}
                className="grid grid-cols-3 gap-6 mb-16 max-w-4xl"
              >
                {quickTemplates.map((template) => (
                  <motion.button
                    key={template.id}
                    whileHover={{
                      scale: 1.02,
                      boxShadow: "0 0 30px rgba(168, 85, 247, 0.2)",
                    }}
                    transition={{ duration: 0.2 }}
                    onClick={() => handleTemplateClick(template.title)}
                    className="group text-left p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-purple-400/50 transition-all duration-200"
                  >
                    <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 group-hover:bg-white/10 transition-colors">
                      <template.icon className="w-6 h-6 text-gray-400 group-hover:text-purple-400 transition-colors" />
                    </div>
                    <h3 className="text-gray-200 font-semibold text-lg mb-2 group-hover:text-white transition-colors">
                      {template.title}
                    </h3>
                    <p className="text-gray-500 text-sm leading-relaxed">
                      {template.description}
                    </p>
                  </motion.button>
                ))}
              </motion.div>
            </motion.div>
          )}

          {/* 状态 B: 加载状态 */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex-1 flex flex-col items-center justify-center"
            >
              <div className="flex flex-col items-center gap-6">
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  <div className="relative">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-cyan-400 flex items-center justify-center">
                      <Brain className="w-12 h-12 text-white" />
                    </div>
                    <div className="absolute inset-0 rounded-full border-4 border-purple-500/30 animate-ping" />
                  </div>
                </motion.div>
                
                <div className="text-center">
                  <motion.h2
                    animate={{
                      opacity: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                    className="text-2xl font-bold text-gray-200 mb-2"
                  >
                    AI 智能体矩阵正在生成策划案...
                  </motion.h2>
                  <p className="text-gray-500">
                    多 Agent 协作中，请稍候
                  </p>
                </div>

                {/* 流光骨架屏 */}
                <div className="w-full max-w-2xl mt-8 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.2 }}
                      className="h-20 bg-gradient-to-r from-purple-500/10 via-cyan-500/10 to-purple-500/10 rounded-2xl overflow-hidden relative"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-[shimmer_2s_infinite]" />
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* 状态 C: 结果展示 */}
          {!isLoading && liveData && (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="flex-1 overflow-y-auto pt-4"
            >
              <div className="max-w-6xl mx-auto space-y-6">
                {/* 标题 */}
                <motion.div variants={itemVariants}>
                  <h2 className="text-3xl font-bold text-white mb-2">
                    {liveData.topic}
                  </h2>
                  <p className="text-gray-400">直播策划已生成完成</p>
                </motion.div>

                {/* Bento Box 布局 */}
                <div className="grid grid-cols-3 gap-6">
                  {/* 左侧大卡片 - 直播大纲 */}
                  <motion.div
                    variants={itemVariants}
                    className="col-span-2"
                  >
                    <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-400 flex items-center justify-center">
                          <Zap className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-xl font-semibold text-white">直播大纲</h3>
                      </div>
                      <div className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                        {liveData.director_outline}
                      </div>

                      {/* 商业资产按钮 */}
                      <motion.div className="mt-6 pt-6 border-t border-white/10">
                        <button
                          onClick={handleGenerateAssets}
                          disabled={isGeneratingAssets}
                          className="group relative inline-flex items-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isGeneratingAssets ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          ) : (
                            <Sparkles className="w-5 h-5 text-white" />
                          )}
                          <span className="text-white font-medium">
                            {isGeneratingAssets ? "提取中..." : "✨ 一键提取商业资产"}
                          </span>
                        </button>
                      </motion.div>
                    </div>
                  </motion.div>

                  {/* 右侧卡片 - 动作队列 */}
                  <motion.div
                    variants={itemVariants}
                    className="col-span-1"
                  >
                    <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-400 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                          </div>
                          <h3 className="text-xl font-semibold text-white">动作队列</h3>
                        </div>
                        <button
                          onClick={() => {
                            setCurrentLineIndex(0);
                            setIsTeleprompterOpen(true);
                          }}
                          className="group p-2 rounded-xl bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 transition-all duration-200 shadow-lg shadow-cyan-500/25"
                          title="进入提词器模式"
                        >
                          <MonitorPlay className="w-5 h-5 text-white" />
                        </button>
                      </div>
                      <div className="space-y-3 max-h-[600px] overflow-y-auto mb-6">
                        {liveData.action_queue.map((item, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className={`p-3 rounded-xl border ${
                              item.type === "text" 
                                ? "bg-purple-500/10 border-purple-500/30" 
                                : "bg-cyan-500/10 border-cyan-500/30"
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                item.type === "text" 
                                  ? "bg-purple-500/30 text-purple-300" 
                                  : "bg-cyan-500/30 text-cyan-300"
                              }`}>
                                {item.type === "text" ? "口播" : "场景"}
                              </span>
                            </div>
                            <p className="mt-2 text-sm text-gray-300">
                              {item.type === "text" ? item.content : item.scene}
                            </p>
                          </motion.div>
                        ))}
                      </div>

                      {/* 复盘报告按钮 */}
                      <motion.div className="pt-4 border-t border-white/10">
                        <button
                          onClick={handleGenerateJudge}
                          disabled={isGeneratingJudge}
                          className="group w-full inline-flex items-center justify-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-800 hover:from-cyan-500 hover:to-cyan-700 transition-all duration-200 shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isGeneratingJudge ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          ) : (
                            <Activity className="w-5 h-5 text-white" />
                          )}
                          <span className="text-white font-medium">
                            {isGeneratingJudge ? "生成中..." : "📈 生成直播体检报告"}
                          </span>
                        </button>
                      </motion.div>
                    </div>
                  </motion.div>
                </div>

                {/* 商业资产卡片 */}
                <AnimatePresence>
                  {businessAssets && (
                    <motion.div
                      variants={containerVariants}
                      initial="hidden"
                      animate="visible"
                      className="space-y-4"
                    >
                      <motion.div variants={itemVariants} className="flex items-center gap-3">
                        <Wand2 className="w-6 h-6 text-purple-400" />
                        <h3 className="text-xl font-semibold text-white">商业变现资产</h3>
                      </motion.div>
                      <div className="grid grid-cols-3 gap-6">
                        {/* 课程讲义 */}
                        <motion.div variants={itemVariants} className="col-span-1">
                          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl h-full">
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                                <BookOpen className="w-5 h-5 text-white" />
                              </div>
                              <h4 className="text-lg font-semibold text-white">课程讲义</h4>
                            </div>
                            <div className="text-gray-300 text-sm leading-relaxed max-h-96 overflow-y-auto">
                              <ReactMarkdown>{businessAssets.course_material}</ReactMarkdown>
                            </div>
                          </div>
                        </motion.div>

                        {/* 小红书文案 */}
                        <motion.div variants={itemVariants} className="col-span-1">
                          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl h-full">
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-pink-500 flex items-center justify-center">
                                <ShoppingBag className="w-5 h-5 text-white" />
                              </div>
                              <h4 className="text-lg font-semibold text-white">小红书文案</h4>
                            </div>
                            <div className="text-gray-300 text-sm leading-relaxed max-h-96 overflow-y-auto">
                              <ReactMarkdown>{businessAssets.xiaohongshu}</ReactMarkdown>
                            </div>
                          </div>
                        </motion.div>

                        {/* 短视频脚本 */}
                        <motion.div variants={itemVariants} className="col-span-1">
                          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl h-full">
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                                <Video className="w-5 h-5 text-white" />
                              </div>
                              <h4 className="text-lg font-semibold text-white">短视频脚本</h4>
                            </div>
                            <div className="text-gray-300 text-sm leading-relaxed max-h-96 overflow-y-auto">
                              <ReactMarkdown>{businessAssets.douyin}</ReactMarkdown>
                            </div>
                          </div>
                        </motion.div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* 复盘报告 */}
                <AnimatePresence>
                  {judgeReport && (
                    <motion.div
                      variants={containerVariants}
                      initial="hidden"
                      animate="visible"
                      className="space-y-4"
                    >
                      <motion.div variants={itemVariants} className="flex items-center gap-3">
                        <Activity className="w-6 h-6 text-cyan-400" />
                        <h3 className="text-xl font-semibold text-white">直播体检报告</h3>
                      </motion.div>
                      <div className="grid grid-cols-2 gap-6">
                        {/* 雷达图 */}
                        <motion.div variants={itemVariants}>
                          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl">
                            <h4 className="text-lg font-semibold text-white mb-4">核心指标雷达</h4>
                            <div className="h-80">
                              <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#6b7280" }} />
                                  <Radar
                                    name="评分"
                                    dataKey="A"
                                    stroke="#a855f7"
                                    strokeWidth={2}
                                    fill="#a855f7"
                                    fillOpacity={0.4}
                                  />
                                  <Tooltip
                                    contentStyle={{
                                      backgroundColor: "rgba(0,0,0,0.8)",
                                      border: "1px solid rgba(255,255,255,0.1)",
                                      borderRadius: "8px",
                                    }}
                                  />
                                </RadarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        </motion.div>

                        {/* 详细报告 */}
                        <motion.div variants={itemVariants}>
                          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl">
                            <h4 className="text-lg font-semibold text-white mb-4">详细复盘</h4>
                            <div className="text-gray-300 text-sm leading-relaxed max-h-96 overflow-y-auto whitespace-pre-wrap">
                              {judgeReport.full_report}
                            </div>
                          </div>
                        </motion.div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}

          {/* 底部输入框（始终显示） */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="w-full max-w-4xl mx-auto mt-auto"
          >
            <form
              onSubmit={handleSubmit}
              className="relative"
            >
              {/* Gradient Border */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/50 via-cyan-500/50 to-purple-500/50 p-[1px] blur-sm opacity-50" />
              
              <div className="relative flex items-center gap-4 px-5 py-4 rounded-full bg-[#080808] border border-white/10">
                <Sparkles className="w-6 h-6 text-cyan-400 animate-pulse" />
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="输入你想直播的技术主题，例如：如何用 Next.js 构建企业级 SaaS..."
                  className="flex-1 bg-transparent border-none outline-none text-gray-300 placeholder-gray-600 text-base"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="p-3 rounded-xl bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Send className="w-5 h-5 text-white" />
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      </main>

      {/* VIP 助教悬浮按钮和对话框 */}
      <div className="fixed bottom-8 right-8 z-50">
        <AnimatePresence>
          {isTutorOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="absolute bottom-20 right-0 w-[420px] h-[600px] rounded-2xl bg-white/[0.02] border border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden"
            >
              {/* 聊天窗头部 */}
              <div className="flex items-center justify-between p-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-400 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">VIP 智能助教</h3>
                    <p className="text-gray-500 text-xs">基于课程讲义的 RAG 问答</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsTutorOpen(false)}
                  className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>

              {/* 消息区域 */}
              <div className="flex-1 p-4 space-y-4 overflow-y-auto h-[450px]">
                {tutorMessages.length === 0 ? (
                  <div className="text-center text-gray-500 py-12">
                    <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                    <p>请开始提问，我会基于课程讲义为您解答</p>
                  </div>
                ) : (
                  tutorMessages.map((message, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-2xl ${
                          message.role === "user"
                            ? "bg-gradient-to-r from-purple-600 to-purple-800 text-white rounded-tr-sm"
                            : "bg-white/[0.05] border border-white/10 text-gray-300 rounded-tl-sm"
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>
                    </motion.div>
                  ))
                )}
                {isTutorTyping && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="bg-white/[0.05] border border-white/10 p-3 rounded-2xl rounded-tl-sm">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* 输入区域 */}
              <div className="p-4 border-t border-white/10">
                <form onSubmit={handleTutorSubmit} className="flex gap-3">
                  <input
                    type="text"
                    value={tutorInput}
                    onChange={(e) => setTutorInput(e.target.value)}
                    placeholder="输入您的问题..."
                    className="flex-1 px-4 py-2.5 rounded-xl bg-white/[0.05] border border-white/10 text-gray-300 placeholder-gray-600 outline-none focus:border-purple-500/50 transition-colors"
                    disabled={!businessAssets}
                  />
                  <button
                    type="submit"
                    disabled={isTutorTyping || !tutorInput.trim() || !businessAssets}
                    className="p-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5 text-white" />
                  </button>
                </form>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 悬浮按钮 */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsTutorOpen(!isTutorOpen)}
          disabled={!businessAssets?.course_material}
          className={`relative p-4 rounded-2xl shadow-lg transition-all duration-300 ${
            businessAssets?.course_material
              ? "bg-gradient-to-br from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 shadow-purple-500/25"
              : "bg-gray-800 cursor-not-allowed opacity-50"
          }`}
          title={businessAssets?.course_material ? "与 VIP 智能助教对话" : "请先提取商业资产/课程讲义"}
        >
          <MessageCircle className="w-6 h-6 text-white" />
          {businessAssets?.course_material && (
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-cyan-400 border-2 border-[#050505] animate-pulse" />
          )}
        </motion.button>
      </div>

      {/* 提词器模态框 */}
      <AnimatePresence>
        {isTeleprompterOpen && liveData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-50 bg-black"
          >
            {/* 关闭按钮 */}
            <motion.button
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              onClick={() => setIsTeleprompterOpen(false)}
              className="absolute top-6 right-6 p-3 rounded-xl bg-white/10 hover:bg-white/20 transition-colors z-10"
            >
              <X className="w-6 h-6 text-white" />
            </motion.button>

            {/* 提词器内容 */}
            <div
              ref={teleprompterRef}
              className="max-w-4xl mx-auto h-full overflow-y-auto pb-64 pt-32"
            >
              <div className="px-8">
                {liveData.action_queue.map((item, index) => (
                  <motion.div
                    key={index}
                    data-line-index={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.02 }}
                    onClick={() => setCurrentLineIndex(index)}
                    className="cursor-pointer"
                  >
                    {item.type === "text" ? (
                      <p
                        className={`text-4xl leading-relaxed font-bold tracking-wide transition-all duration-300 ${
                          index === currentLineIndex
                            ? "text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.6)]"
                            : index < currentLineIndex
                            ? "text-gray-800"
                            : "text-gray-500"
                        }`}
                      >
                        {item.content}
                      </p>
                    ) : (
                      <div className="w-fit mx-auto my-8 px-6 py-2 rounded-full border border-cyan-500 bg-cyan-500/10 text-cyan-400 text-sm tracking-widest flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        <span>[ 🎬 导播动作: {item.scene} ]</span>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>

            {/* 键盘快捷键提示 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center gap-6 text-gray-600 text-sm"
            >
              <span className="flex items-center gap-2">
                <kbd className="px-2 py-1 rounded bg-white/10 border border-white/20">Space</kbd>
                <span>下一句</span>
              </span>
              <span className="flex items-center gap-2">
                <kbd className="px-2 py-1 rounded bg-white/10 border border-white/20">↑</kbd>
                <span>上一句</span>
              </span>
              <span className="flex items-center gap-2">
                <kbd className="px-2 py-1 rounded bg-white/10 border border-white/20">Esc</kbd>
                <span>退出</span>
              </span>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
