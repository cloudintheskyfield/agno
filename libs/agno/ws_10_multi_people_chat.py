"""
🎭 多人聊天讨论系统

基于 Agno 框架的多人 AI Agent 讨论系统，支持实时流式输出和 Rich 美化界面。

功能特性:
- 可配置的 AI Agent 角色系统（通过 characters_config.json 配置）
- 顺序发言模式：成员们一个接一个发言，每个人都能看到前面所有人的发言
- Rich 库美化界面，彩色面板和表格显示
- 详细的角色设定：身份、性格、专业领域、说话风格、口头禅等
- 可自定义讨论话题和轮次数量
- 可选启用搜索工具获取实时信息

使用方法:
1. 交互式启动: python ws_10_multi_people_chat.py
2. 演示模式: python ws_10_multi_people_chat.py demo
3. 配置管理: python config_manager.py

配置文件:
- characters_config.json: 角色配置文件
  包含角色的详细设定（身份、性格、专业领域、说话风格等）
  
角色配置字段:
- name: 角色名称
- title: 角色标题
- emoji: 角色表情
- color: 显示颜色
- style: 文本样式
- 身份设定: 角色的身份背景
- 性格特点: 角色的性格特征
- 喜好: 角色的兴趣爱好
- 说话风格: 角色的表达方式
- 专业领域: 角色的专业知识
- 口头禅: 角色的标志性用语
- 背景故事: 角色的详细背景

依赖库:
- agno (AI Agent 框架)
- rich (终端美化)
- 其他标准库

作者: AI Assistant
版本: 3.0 (配置化角色版)
"""

# 首先禁用所有 metrics 输出
import disable_metrics

from agno.team import Team
from agno.agent import Agent
from agno.run.agent import RunEvent
from agno.vllm import q72b, q3o
from agno.tools.duckduckgo import DuckDuckGoTools
from typing import List, Optional, Dict, Any
import random
import time
import json
import re
import os

# Rich 库用于美化输出
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.columns import Columns
from rich.align import Align


DEFAULT_DISCUSSION_SETTINGS: Dict[str, Any] = {
    "default_max_rounds": 3,
    "default_enable_search": True,
    "speech_length": "100-150字",
    "discussion_style": "sequential"
}

TOTAL_DISCUSSION_CHAR_RANGE = (400, 600)  # 合计目标字符数，约10秒生成量

DEFAULT_CHARACTER_FIELD_DEFAULTS: Dict[str, Any] = {
    "emoji": "💬",
    "color": "bright_white",
    "style": "bold bright_white",
    "身份设定": "未设定",
    "性格特点": "未设定",
    "专业领域": "未设定",
    "喜好": "未设定",
    "说话风格": "未设定",
    "口头禅": "未设定",
    "背景故事": "未设定"
}

class MultiPeopleChat:
    """多人聊天讨论系统"""

    def __init__(
        self,
        topic: str,
        max_rounds: Optional[int] = None,
        enable_search: Optional[bool] = None,
        config_path: Optional[str] = None,
        use_fallback_model: bool = False,
    ):
        """
        初始化多人聊天系统

        Args:
            topic: 讨论话题
            max_rounds: 最大讨论轮次
            enable_search: 是否启用搜索工具
            use_fallback_model: 是否使用备用模型（当主模型限流时）
        """
        # 初始化 Rich Console
        self.console = Console()

        # 配置文件路径
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'characters_config.json')

        # 基础属性
        self.topic = topic
        self.current_round = 0
        self.discussion_history = []
        
        # 模型选择
        self.model = q3o if use_fallback_model else q72b

        # 加载配置
        self.agent_configs, self.settings = self._load_configuration()

        # 应用可选的外部设置
        self.max_rounds = max_rounds if max_rounds is not None else self.settings['default_max_rounds']
        self.enable_search = (
            enable_search if enable_search is not None else self.settings['default_enable_search']
        )

        # 创建不同角色的 Agent
        self.agents = self._create_agents()

        # 创建 Team
        self.team = self._create_team()

        # 显示初始化信息
        self._show_welcome()

    def _load_configuration(self) -> tuple[List[dict], Dict[str, Any]]:
        """加载并校验配置文件"""

        config_data: Dict[str, Any] = {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            self.console.print("[yellow]⚠️ 配置文件未找到，将使用内置默认配置[/yellow]")
        except json.JSONDecodeError as e:
            self.console.print(f"[red]❌ 配置文件格式错误: {e}。将回退到默认配置。[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ 加载配置文件失败: {e}。将回退到默认配置。[/red]")

        raw_characters = config_data.get('characters') if isinstance(config_data, dict) else None
        raw_settings = config_data.get('discussion_settings') if isinstance(config_data, dict) else None

        # 处理讨论配置
        settings = DEFAULT_DISCUSSION_SETTINGS.copy()
        if isinstance(raw_settings, dict):
            settings.update({k: raw_settings[k] for k in raw_settings if k in settings})

        # 校验轮次（必须为正整数）
        try:
            settings['default_max_rounds'] = int(settings['default_max_rounds'])
            if settings['default_max_rounds'] <= 0:
                raise ValueError
        except (TypeError, ValueError):
            self.console.print("[yellow]⚠️ default_max_rounds 配置无效，已重置为 3[/yellow]")
            settings['default_max_rounds'] = DEFAULT_DISCUSSION_SETTINGS['default_max_rounds']

        # 校验布尔值
        settings['default_enable_search'] = bool(settings.get('default_enable_search', True))

        # 校验讨论模式
        if settings.get('discussion_style') not in {"sequential"}:
            self.console.print("[yellow]⚠️ 当前仅支持 sequential 讨论模式，已自动重置[/yellow]")
            settings['discussion_style'] = DEFAULT_DISCUSSION_SETTINGS['discussion_style']

        # 处理角色配置
        validated_characters: List[dict] = []

        if isinstance(raw_characters, list):
            for idx, char in enumerate(raw_characters, 1):
                if not isinstance(char, dict):
                    self.console.print(f"[yellow]⚠️ 第 {idx} 个角色配置不是对象，已跳过[/yellow]")
                    continue

                name = char.get('name')
                title = char.get('title')
                if not name or not title:
                    self.console.print(f"[yellow]⚠️ 第 {idx} 个角色缺少 name/title，已跳过[/yellow]")
                    continue

                merged = DEFAULT_CHARACTER_FIELD_DEFAULTS.copy()
                merged.update(char)

                # 自动匹配样式
                color = merged.get('color') or DEFAULT_CHARACTER_FIELD_DEFAULTS['color']
                merged['color'] = color
                merged['style'] = merged.get('style') or f"bold {color}"

                validated_characters.append(merged)

        if not validated_characters:
            self.console.print("[yellow]⚠️ 未找到有效的角色配置，使用默认角色列表[/yellow]")
            validated_characters = self._get_default_configs()

        return validated_characters, settings

    def _get_default_configs(self) -> List[dict]:
        """获取默认角色配置"""
        
        return [
            {
                "name": "Alice",
                "title": "乐观主义者",
                "color": "bright_green",
                "emoji": "🌟",
                "style": "bold bright_green",
                "身份设定": "一位充满正能量的心理咨询师",
                "性格特点": "积极向上、善于鼓励他人",
                "喜好": "阅读励志书籍、帮助他人成长",
                "说话风格": "温暖友善、充满希望",
                "专业领域": "心理学、人际关系",
                "口头禅": "每个挑战都是成长的机会！",
                "背景故事": "专业心理咨询师，帮助过数百人走出困境"
            },
            {
                "name": "Bob",
                "title": "现实主义者",
                "color": "bright_blue",
                "emoji": "📊",
                "style": "bold bright_blue",
                "身份设定": "资深数据分析师和商业顾问",
                "性格特点": "理性客观、注重事实",
                "喜好": "研究市场趋势、收集统计数据",
                "说话风格": "逻辑清晰、引用数据",
                "专业领域": "数据分析、商业策略",
                "口头禅": "让数据来说话！",
                "背景故事": "在多家知名企业担任过数据分析师"
            },
            {
                "name": "Charlie",
                "title": "批判思考者",
                "color": "bright_yellow",
                "emoji": "🤔",
                "style": "bold bright_yellow",
                "身份设定": "哲学教授和独立思考者",
                "性格特点": "深思熟虑、善于质疑",
                "喜好": "哲学辩论、逻辑推理",
                "说话风格": "严谨理性、喜欢提出反问",
                "专业领域": "哲学、逻辑学",
                "口头禅": "这个结论真的站得住脚吗？",
                "背景故事": "哲学教授，致力于培养独立思考能力"
            },
            {
                "name": "Diana",
                "title": "创新者",
                "color": "bright_magenta",
                "emoji": "💡",
                "style": "bold bright_magenta",
                "身份设定": "科技创业者和未来学家",
                "性格特点": "富有想象力、勇于尝试",
                "喜好": "科幻小说、新技术体验",
                "说话风格": "充满创意、经常提出新颖观点",
                "专业领域": "科技创新、未来趋势",
                "口头禅": "如果我们换个角度思考呢？",
                "背景故事": "创办过多家科技公司的未来学演讲者"
            }
        ]

    def _show_welcome(self):
        """显示欢迎界面"""

        # 创建标题
        title = Text("🎭 多人聊天讨论系统", style="bold bright_cyan", justify="center")

        # 创建信息表格
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_row("🎯 讨论话题:", f"[bold]{self.topic}[/bold]")
        info_table.add_row("📊 最大轮次:", f"[bold]{self.max_rounds}[/bold]")
        info_table.add_row("🔍 搜索工具:", f"[bold]{'启用' if self.enable_search else '禁用'}[/bold]")

        # 创建参与者信息
        participants = []
        for config in self.agent_configs:
            participant = Text()
            participant.append(f"{config['emoji']} {config['name']}", style=config['style'])
            participant.append(f" - {config['title']}", style="dim")
            participants.append(participant)

        # 添加使用提示
        tip_text = Text()
        tip_text.append("💡 提示: ", style="bold bright_yellow")
        tip_text.append("采用顺序发言模式，成员们会一个接一个发言，", style="dim")
        tip_text.append("每个人都能看到前面所有人的发言内容", style="dim")

        # 显示欢迎面板
        welcome_content = Columns([
            Align.center(info_table),
            Align.center(Text("\n").join(participants))
        ], equal=True)

        welcome_panel = Panel(
            Align.center(welcome_content),
            title=title,
            border_style="bright_cyan",
            padding=(1, 2)
        )

        self.console.print(welcome_panel)

        # 显示提示
        tip_panel = Panel(
            Align.center(tip_text),
            border_style="yellow",
            padding=(0, 1)
        )
        self.console.print(tip_panel)
        self.console.print()

    def _create_agents(self) -> List[Agent]:
        """创建不同角色的 Agent"""

        # 搜索工具（如果启用）
        search_tools = [DuckDuckGoTools()] if self.enable_search else []

        agents = []

        for config in self.agent_configs:
            # 构建详细的角色描述
            role_description = f"""
你是 {config['name']} - {config['title']}。

【角色设定】
- 身份：{config.get('身份设定', '未设定')}
- 性格特点：{config.get('性格特点', '未设定')}
- 专业领域：{config.get('专业领域', '未设定')}
- 喜好：{config.get('喜好', '未设定')}
- 说话风格：{config.get('说话风格', '未设定')}
- 口头禅：{config.get('口头禅', '未设定')}
- 背景故事：{config.get('背景故事', '未设定')}

在讨论'{self.topic}'时，请根据你的角色设定来发言，保持角色的一致性和个性化特点。
"""

            agent = Agent(
                name=f"{config['name']} - {config['title']}",
                role=role_description,
                model=self.model,
                tools=search_tools if self.enable_search else [],
                markdown=True
            )
            agents.append(agent)

        return agents

    def _create_team(self) -> Team:
        """创建讨论团队"""

        team = Team(
            name="多人讨论团队",
            members=self.agents,
            model=self.model,
            # 配置团队行为
            delegate_task_to_all_members=False,  # 禁用自动委托
            determine_input_for_members=False,  # 直接发送输入给成员，不让 leader 决策
            respond_directly=True,  # 成员直接响应，不经过 leader 处理
            tool_choice="auto",  # 允许使用工具
            markdown=True,
            # 存储事件以便分析
            store_events=True,
            store_member_responses=True  # 存储成员响应
        )

        return team

    def start_discussion(self, stream: bool = False) -> None:
        """开始讨论"""

        # 显示开始讨论的标题
        start_panel = Panel(
            Align.center(f"🚀 开始讨论: [bold bright_cyan]{self.topic}[/bold bright_cyan]"),
            border_style="bright_green",
            padding=(0, 2)
        )
        self.console.print(start_panel)
        self.console.print()

        for round_num in range(1, self.max_rounds + 1):
            self.current_round = round_num

            # 显示轮次标题
            round_title = f"🔄 第 {round_num} 轮讨论"
            round_panel = Panel(
                Align.center(round_title),
                border_style="bright_yellow",
                padding=(0, 2)
            )
            self.console.print(round_panel)

            try:
                if stream:
                    self._run_streaming_discussion(round_num)
                else:
                    # 使用顺序发言模式（非流式，随机顺序）
                    self._run_sequential_discussion(round_num)

                # 添加延迟避免过快请求
                if round_num < self.max_rounds:
                    with self.console.status("[bold green]准备下一轮讨论...", spinner="dots"):
                        time.sleep(2)

            except Exception as e:
                error_panel = Panel(
                    f"❌ 第 {round_num} 轮讨论出错: {e}",
                    border_style="red",
                    title="错误"
                )
                self.console.print(error_panel)
                break

        # 显示讨论结束
        end_panel = Panel(
            Align.center(f"🎉 讨论结束！共进行了 [bold]{self.current_round}[/bold] 轮"),
            border_style="bright_green",
            padding=(0, 2)
        )
        self.console.print(end_panel)
        self._show_summary()

    def _create_initial_prompt(self) -> str:
        """创建初始讨论提示"""

        prompt = f"""
我们要讨论的话题是：{self.topic}

请每个团队成员根据自己的角色和观点，对这个话题发表看法：

1. Alice（乐观主义者）：请从积极正面的角度分析这个话题
2. Bob（现实主义者）：请提供客观的事实和数据分析
3. Charlie（批判思考者）：请指出可能存在的问题和挑战
4. Diana（创新者）：请提出创新的想法和解决方案

每人发言控制在100-150字，要有自己独特的观点。这是第1轮讨论，共{self.max_rounds}轮。
"""
        return prompt

    def _create_follow_up_prompt(self) -> str:
        """创建后续轮次的提示"""

        previous_rounds = "\n\n".join([
            f"第{round_data['round']}轮内容:\n{round_data['content']}"
            for round_data in self.discussion_history
        ])

        if not previous_rounds:
            previous_rounds = "暂无历史发言。"

        prompt = f"""
基于前面的讨论，我们继续深入探讨：{self.topic}

这是第{self.current_round}轮讨论（共{self.max_rounds}轮）。

之前的讨论历史：
{previous_rounds}

请每个成员：
1. 回应其他成员的观点
2. 提出新的见解或问题
3. 推进讨论的深度

保持各自的角色特点，每人发言100-150字。
"""
        return prompt

    def _run_sequential_discussion(self, round_num: int) -> None:
        """运行非流式顺序讨论，随机发言顺序"""

        # 初始化讨论历史
        round_discussion = ""

        # 随机打乱当轮发言顺序
        speakers = list(zip(self.agents, self.agent_configs))
        random.shuffle(speakers)

        # 记录本轮顺序方便总结
        speaker_order = []

        total_min_chars, total_max_chars = TOTAL_DISCUSSION_CHAR_RANGE
        speaker_count = max(1, len(speakers))
        per_speaker_min = max(60, total_min_chars // speaker_count)
        per_speaker_max = max(per_speaker_min + 30, total_max_chars // speaker_count)
        length_guidance = (
            f"请控制在{per_speaker_min}-{per_speaker_max}字内，"
            f"确保所有成员合计约为{total_min_chars}-{total_max_chars}字，整体生成时长不超过10秒。"
        )

        # 为每个 Agent 创建个性化的提示
        for i, (agent, config) in enumerate(speakers):

            speaker_order.append(config['name'])

            # 显示当前发言者
            speaker_indicator = Panel(
                Align.center(f"{config['emoji']} {config['name']} 正在发言..."),
                border_style=config['color'],
                padding=(0, 2)
            )
            self.console.print(speaker_indicator)

            # 创建个性化提示
            if round_num == 1:
                if i == 0:
                    # 第一个人的提示
                    prompt = f"""
我们要讨论的话题是：{self.topic}

你是 {config['name']} - {config['title']}。请根据你的角色特点，对这个话题发表你的看法。

{self._get_role_description(config['name'])}

{length_guidance}
请务必遵守长度上限。
"""
                else:
                    # 后续发言者的提示
                    prompt = f"""
我们正在讨论：{self.topic}

前面的发言内容：
{round_discussion}

你是 {config['name']} - {config['title']}。请根据你的角色特点，回应前面的发言并表达你的观点。

{self._get_role_description(config['name'])}

{length_guidance}
请确保回应前面提到的关键观点，并延伸新的思路；不要超过长度上限。
"""
            else:
                # 后续轮次的提示
                previous_rounds = "\n\n".join([f"第{j+1}轮讨论:\n{round_data['content']}"
                                             for j, round_data in enumerate(self.discussion_history)])

                prompt = f"""
我们正在进行第{round_num}轮讨论，话题是：{self.topic}

之前的讨论历史：
{previous_rounds}

本轮前面的发言：
{round_discussion}

你是 {config['name']} - {config['title']}。请根据你的角色特点，继续参与讨论。

{self._get_role_description(config['name'])}

{length_guidance}
请确保：
1. 回应其他成员的观点
2. 提出新的见解
3. 推进讨论深度
请保持在长度上限内。
"""

            try:
                # 让单个 Agent 发言
                agent_response = agent.run(prompt)

                # 显示发言内容
                content = agent_response.content if hasattr(agent_response, 'content') else str(agent_response)
                content = content.strip()

                if len(content) > per_speaker_max:
                    content = content[:per_speaker_max].rstrip() + "..."

                # 创建发言者标题
                speaker_title = Text()
                speaker_title.append(f"{config['emoji']} {config['name']}", style=config['style'])
                speaker_title.append(f" - {config['title']}", style="dim")

                message_panel = Panel(
                    Markdown(content),
                    title=speaker_title,
                    border_style=config['color'],
                    padding=(0, 1)
                )
                self.console.print(message_panel)

                # 记录发言内容
                speaker_content = f"**{config['name']}**: {content}\n\n"
                round_discussion += speaker_content

                # 显示发言完成
                complete_indicator = Panel(
                    Align.center(f"✅ {config['name']} 发言完成"),
                    border_style="bright_green",
                    padding=(0, 1)
                )
                self.console.print(complete_indicator)
                self.console.print()

            except Exception as e:
                error_panel = Panel(
                    f"❌ {config['name']} 发言失败: {e}",
                    border_style="red",
                    title="错误"
                )
                self.console.print(error_panel)
                continue

        # 保存这轮讨论
        self.discussion_history.append({
            'round': round_num,
            'content': round_discussion,
            'timestamp': time.time(),
            'order': speaker_order
        })

    def _get_role_description(self, agent_name: str) -> str:
        """获取角色描述"""
        
        # 从配置中找到对应的角色
        for config in self.agent_configs:
            if config['name'] == agent_name:
                description = f"""
你的角色设定：
- 身份：{config.get('身份设定', '未设定')}
- 性格特点：{config.get('性格特点', '未设定')}
- 专业领域：{config.get('专业领域', '未设定')}
- 喜好：{config.get('喜好', '未设定')}
- 说话风格：{config.get('说话风格', '未设定')}
- 口头禅：{config.get('口头禅', '未设定')}
- 背景故事：{config.get('背景故事', '未设定')}

请根据以上设定来发言，保持角色的一致性和个性化特点。
"""
                return description
        
        return "请根据你的角色特点发言。"

    def _parse_speaker_content(self, content: str) -> list:
        """解析发言内容，识别发言者"""

        # 尝试匹配发言者模式
        patterns = [
            r'\*\*([^*]+)\*\*[：:]\s*(.*?)(?=\*\*[^*]+\*\*[：:]|$)',  # **Name**: content
            r'([^：:]+)[：:]\s*(.*?)(?=\n[^：:]+[：:]|$)',  # Name: content
            r'(\w+)\s*[-–]\s*([^：:]+)[：:]\s*(.*?)(?=\n\w+\s*[-–]|$)'  # Name - Title: content
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches:
                return matches

        return []

    def _detect_complete_speech(self, content: str, speaker_name: str) -> bool:
        """检测发言是否完整（以句号、感叹号、问号等结尾）"""

        if not content.strip():
            return False

        # 检查是否以句子结束符结尾
        ending_patterns = [
            r'[。！？\.!?]\s*$',  # 中英文句号、感叹号、问号
            r'[。！？\.!?]\s*\n\s*$',  # 句子结束符后跟换行
            r'[。！？\.!?]\s*\*\*',  # 句子结束符后跟下一个发言者
        ]

        for pattern in ending_patterns:
            if re.search(pattern, content):
                return True

        # 检查内容长度，如果超过一定长度且包含完整句子，认为是完整发言
        if len(content.strip()) > 50:
            sentence_count = len(re.findall(r'[。！？\.!?]', content))
            if sentence_count >= 1:
                return True

        return False

    def _get_speaker_config(self, speaker_name: str):
        """根据发言者名称获取配置"""

        for config in self.agent_configs:
            if config['name'].lower() in speaker_name.lower() or speaker_name.lower() in config['name'].lower():
                return config

        # 默认配置
        return {
            "name": speaker_name,
            "title": "参与者",
            "color": "white",
            "emoji": "💬",
            "style": "bold white"
        }

    def _build_speaker_panel(self, config: dict, content: str, is_complete: bool) -> Panel:
        """构建发言面板，可用于静态展示或实时刷新"""

        speaker_title = Text()
        speaker_title.append(f"{config['emoji']} {config['name']}", style=config['style'])
        speaker_title.append(f" - {config['title']}", style="dim")
        speaker_title.append(" ✓" if is_complete else " ...", style="bright_green" if is_complete else "dim")

        clean_content = (content or "").strip()
        if not clean_content:
            clean_content = "_正在组织语言..._"

        return Panel(
            Markdown(clean_content),
            title=speaker_title,
            border_style=config.get('color', 'white'),
            padding=(0, 1)
        )

    def _display_speaker_message(self, speaker_name: str, content: str, is_complete: bool = False):
        """显示发言者消息"""

        config = self._get_speaker_config(speaker_name)
        message_panel = self._build_speaker_panel(config, content, is_complete)
        self.console.print(message_panel)
        self.console.print()

    def _run_streaming_discussion(self, round_num: int) -> None:
        """运行流式讨论（逐个 Agent 流式）"""

        # 显示讨论状态
        status_panel = Panel(
            Align.center("💬 实时讨论进行中..."),
            border_style="bright_blue",
            padding=(0, 2)
        )
        self.console.print(status_panel)

        round_discussion = ""
        speaker_panels: List[Panel] = []
        final_speaker_contents: List[tuple[dict, str]] = []
        incremental_step = 10
        incremental_delay = 0.12

        with Live(console=self.console, refresh_per_second=4) as live_round:
            for index, (agent, config) in enumerate(zip(self.agents, self.agent_configs)):
                # 初始化当前发言者面板
                speaker_config = self._get_speaker_config(config['name'])
                if len(speaker_panels) <= index:
                    speaker_panels.append(self._build_speaker_panel(speaker_config, "", False))
                else:
                    speaker_panels[index] = self._build_speaker_panel(speaker_config, "", False)

                live_round.update(Columns(speaker_panels, equal=True))

                if round_num == 1:
                    if index == 0:
                        prompt = f"""
我们要讨论的话题是：{self.topic}

你是 {config['name']} - {config['title']}。请根据你的角色特点，对这个话题发表你的看法。

{self._get_role_description(config['name'])}

请发言100-150字，表达你的观点。
"""
                    else:
                        prompt = f"""
我们正在讨论：{self.topic}

前面的发言内容：
{round_discussion}

你是 {config['name']} - {config['title']}。请根据你的角色特点，回应前面的发言并表达你的观点。

{self._get_role_description(config['name'])}

请发言100-150字。
"""
                else:
                    previous_rounds = "\n\n".join([
                        f"第{data['round']}轮讨论:\n{data['content']}"
                        for data in self.discussion_history
                    ]) or "暂无历史发言。"

                    prompt = f"""
我们正在进行第{round_num}轮讨论，话题是：{self.topic}

之前的讨论历史：
{previous_rounds}

本轮前面的发言：
{round_discussion}

你是 {config['name']} - {config['title']}。请根据你的角色特点，继续参与讨论。

{self._get_role_description(config['name'])}

请发言100-150字，可以：
1. 回应其他成员的观点
2. 提出新的见解
3. 推进讨论深度
"""

                try:
                    response_stream = agent.run(
                        prompt,
                        stream=True,
                        stream_intermediate_steps=True
                    )

                    speaker_content = ""
                    received_content_events = False

                    for event in response_stream:
                        if not hasattr(event, "event"):
                            continue

                        event_type = event.event

                        if event_type == RunEvent.run_content.value:
                            chunk = getattr(event, "content", None)
                            if chunk:
                                prev_length = len(speaker_content)
                                speaker_content += chunk
                                received_content_events = True

                                # 渐进式展示新增内容
                                target_length = len(speaker_content)
                                cursor = prev_length
                                while cursor < target_length:
                                    cursor = min(cursor + incremental_step, target_length)
                                    partial_content = speaker_content[:cursor]
                                    speaker_panels[index] = self._build_speaker_panel(
                                        speaker_config,
                                        partial_content,
                                        False
                                    )
                                    live_round.update(Columns(speaker_panels, equal=True))
                                    live_round.refresh()
                                    time.sleep(incremental_delay)

                        elif event_type == RunEvent.run_completed.value:
                            final_content = getattr(event, "content", None) or speaker_content
                            if final_content:
                                prev_length = len(speaker_content)
                                speaker_content = final_content

                                if not received_content_events:
                                    cursor = prev_length
                                    target_length = len(speaker_content)
                                    while cursor < target_length:
                                        cursor = min(cursor + incremental_step, target_length)
                                        partial_content = speaker_content[:cursor]
                                        speaker_panels[index] = self._build_speaker_panel(
                                            speaker_config,
                                            partial_content,
                                            cursor == target_length
                                        )
                                        live_round.update(Columns(speaker_panels, equal=True))
                                        live_round.refresh()
                                        if cursor < target_length:
                                            time.sleep(incremental_delay)

                                speaker_panels[index] = self._build_speaker_panel(
                                    speaker_config,
                                    speaker_content,
                                    True
                                )
                                live_round.update(Columns(speaker_panels, equal=True))
                                live_round.refresh()

                        elif event_type == RunEvent.tool_call_started.value:
                            tool_info = getattr(event, "tool", None)
                            tool_name = "工具"
                            if tool_info and hasattr(tool_info, "tool_name"):
                                tool_name = tool_info.tool_name

                            tool_panel = Panel(
                                f"🔍 {tool_name} 调用中...",
                                border_style="cyan",
                                title="工具调用"
                            )
                            self.console.print(tool_panel)

                        elif event_type == RunEvent.tool_call_completed.value:
                            completed_panel = Panel(
                                "✅ 工具调用完成",
                                border_style="green",
                                title="完成"
                            )
                            self.console.print(completed_panel)

                        elif event_type == RunEvent.reasoning_step.value:
                            reasoning_content = getattr(event, "content", None)
                            if reasoning_content:
                                reasoning_panel = Panel(
                                    reasoning_content,
                                    border_style="magenta",
                                    title="💭 思考过程"
                                )
                                self.console.print(reasoning_panel)

                    if speaker_content:
                        round_discussion += f"**{config['name']}**: {speaker_content}\n\n"
                    final_speaker_contents.append((speaker_config, speaker_content))

                except Exception as e:
                    error_panel = Panel(
                        f"❌ {config['name']} 流式发言失败: {e}",
                        border_style="red",
                        title="错误"
                    )
                    self.console.print(error_panel)

        self.discussion_history.append({
            'round': round_num,
            'content': round_discussion,
            'timestamp': time.time()
        })

    def _run_normal_discussion(self, prompt: str) -> None:
        """运行普通讨论"""

        # 显示讨论状态
        with self.console.status("[bold blue]💬 讨论进行中...", spinner="dots"):
            try:
                result = self.team.run(prompt)

                if hasattr(result, 'content'):
                    # 解析并显示发言内容
                    speakers = self._parse_speaker_content(result.content)
                    if speakers:
                        for speaker_info in speakers:
                            if len(speaker_info) >= 2:
                                speaker_name = speaker_info[0].strip()
                                speaker_content = speaker_info[-1].strip()
                                if speaker_content:
                                    is_complete = self._detect_complete_speech(speaker_content, speaker_name)
                                    self._display_speaker_message(speaker_name, speaker_content, is_complete)
                    else:
                        # 如果无法解析，直接显示内容
                        content_panel = Panel(
                            Markdown(result.content),
                            title="💬 讨论内容",
                            border_style="blue"
                        )
                        self.console.print(content_panel)

                    # 保存这轮讨论
                    self.discussion_history.append({
                        'round': self.current_round,
                        'content': result.content,
                        'timestamp': time.time()
                    })

                # 显示完成状态
                complete_panel = Panel(
                    Align.center(f"✅ 第 {self.current_round} 轮讨论完成"),
                    border_style="bright_green",
                    padding=(0, 2)
                )
                self.console.print(complete_panel)

            except Exception as e:
                error_panel = Panel(
                    f"❌ 讨论出错: {e}",
                    border_style="red",
                    title="错误"
                )
                self.console.print(error_panel)

    def _show_summary(self) -> None:
        """显示讨论总结"""

        # 创建总结表格
        summary_table = Table(title="📋 讨论总结", show_header=False, box=None, padding=(0, 2))

        summary_table.add_row("🎯 话题:", f"[bold]{self.topic}[/bold]")
        summary_table.add_row("🔄 轮次:", f"[bold]{len(self.discussion_history)}/{self.max_rounds}[/bold]")

        participants = ', '.join([config['name'] for config in self.agent_configs])
        summary_table.add_row("👥 参与者:", f"[bold]{participants}[/bold]")

        if self.discussion_history:
            total_words = sum(len(round_data['content']) for round_data in self.discussion_history)
            summary_table.add_row("📝 总字数:", f"[bold]{total_words}[/bold]")

            duration = self.discussion_history[-1]['timestamp'] - self.discussion_history[0]['timestamp']
            summary_table.add_row("⏱️ 讨论时长:", f"[bold]{duration:.1f} 秒[/bold]")

        # 创建讨论要点
        highlights = []
        for i, round_data in enumerate(self.discussion_history, 1):
            content_preview = round_data['content'][:100].replace('\n', ' ')
            if len(content_preview) > 97:
                content_preview = content_preview[:97] + "..."

            highlight_text = Text()
            highlight_text.append(f"第{i}轮: ", style="bold bright_cyan")
            highlight_text.append(content_preview, style="dim")
            highlights.append(highlight_text)

        # 显示总结面板
        if highlights:
            summary_content = Columns([
                summary_table,
                Align.left(Text("\n").join(highlights))
            ], equal=True)
        else:
            summary_content = summary_table

        summary_panel = Panel(
            summary_content,
            title=Text("📋 讨论总结", style="bold bright_cyan"),
            border_style="bright_cyan",
            padding=(1, 2)
        )

        self.console.print(summary_panel)

def main():
    """主函数 - 交互式启动讨论"""

    console = Console()

    # 显示欢迎标题
    title_panel = Panel(
        Align.center(Text("🎭 多人聊天讨论系统", style="bold bright_cyan")),
        border_style="bright_cyan",
        padding=(1, 2)
    )
    console.print(title_panel)
    console.print()

    # 获取用户输入
    try:
        topic = console.input("[bold bright_green]请输入讨论话题: [/bold bright_green]").strip()
        if not topic:
            topic = "人工智能对未来社会的影响"
            console.print(f"[dim]使用默认话题: {topic}[/dim]")

        max_rounds_input = console.input("[bold bright_blue]请输入最大讨论轮次 (默认3轮): [/bold bright_blue]").strip()
        max_rounds = int(max_rounds_input) if max_rounds_input.isdigit() else 3

        enable_search_input = console.input("[bold bright_yellow]是否启用搜索工具? (y/n, 默认y): [/bold bright_yellow]").strip().lower()
        enable_search = enable_search_input != 'n'

        stream_input = console.input("[bold bright_magenta]是否使用流式输出? (y/n, 默认y): [/bold bright_magenta]").strip().lower()
        stream = stream_input != 'n'

    except KeyboardInterrupt:
        console.print("\n[bold bright_red]👋 再见！[/bold bright_red]")
        return

    # 创建并启动讨论
    try:
        chat_system = MultiPeopleChat(
            topic=topic,
            max_rounds=max_rounds,
            enable_search=enable_search
        )

        chat_system.start_discussion(stream=stream)

    except Exception as e:
        error_panel = Panel(
            f"❌ 系统错误: {e}\n💡 建议检查网络连接和模型服务状态",
            border_style="red",
            title="错误"
        )
        console.print(error_panel)

def demo():
    """演示函数 - 预设话题快速演示"""

    console = Console()

    # 显示演示标题
    demo_panel = Panel(
        Align.center(Text("🎭 多人聊天讨论系统 - 演示模式", style="bold bright_magenta")),
        border_style="bright_magenta",
        padding=(1, 2)
    )
    console.print(demo_panel)
    console.print()

    # 预设的演示话题
    demo_topics = [
        "远程工作的优缺点",
        "电动汽车的发展前景",
        "社交媒体对青少年的影响",
        "可持续发展与经济增长的平衡"
    ]

    # 创建话题选择表格
    topics_table = Table(title="可选演示话题", show_header=False, box=None)
    for i, topic in enumerate(demo_topics, 1):
        topics_table.add_row(f"[bold bright_cyan]{i}.[/bold bright_cyan]", topic)

    console.print(topics_table)
    console.print()

    try:
        choice = console.input("[bold bright_green]请选择话题编号 (1-4) 或输入自定义话题: [/bold bright_green]").strip()

        if choice.isdigit() and 1 <= int(choice) <= 4:
            topic = demo_topics[int(choice) - 1]
        else:
            topic = choice if choice else demo_topics[0]

        # 使用演示配置
        chat_system = MultiPeopleChat(
            topic=topic,
            max_rounds=2,  # 演示用较少轮次
            enable_search=True
        )

        chat_system.start_discussion(stream=True)

    except KeyboardInterrupt:
        console.print("\n[bold bright_red]👋 演示结束！[/bold bright_red]")
    except Exception as e:
        error_panel = Panel(
            f"❌ 演示出错: {e}",
            border_style="red",
            title="错误"
        )
        console.print(error_panel)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
