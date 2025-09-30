"""
流式响应调试工具
用于打印和分析流式响应的 chunk 内容
"""

import json
import time
from typing import Any, Optional

class StreamDebugger:
    """流式响应调试器"""
    
    def __init__(self, enabled: bool = True, verbose: bool = False):
        self.enabled = enabled
        self.verbose = verbose
        self.chunk_count = 0
        self.total_content_length = 0
        self.start_time = None
        
    def start_stream(self, model_name: str = "Unknown"):
        """开始流式响应调试"""
        if not self.enabled:
            return
            
        self.chunk_count = 0
        self.total_content_length = 0
        self.start_time = time.time()
        
        print(f"\n🚀 开始流式响应 [{model_name}] - {time.strftime('%H:%M:%S')}")
        print("=" * 60)
    
    def log_chunk(self, response_delta: Any, chunk_index: Optional[int] = None):
        """记录单个 chunk"""
        if not self.enabled:
            return
            
        self.chunk_count += 1
        current_chunk = chunk_index or self.chunk_count
        
        # 提取内容
        content = self._extract_content(response_delta)
        
        if content:
            self.total_content_length += len(content)
            
            # 基础信息
            print(f"📦 Chunk #{current_chunk:03d} | 长度: {len(content):3d} | 累计: {self.total_content_length:4d}")
            
            # 内容预览
            if self.verbose:
                # 详细模式：显示完整内容和结构
                print(f"   内容: {repr(content)}")
                print(f"   类型: {type(response_delta).__name__}")
                
                # 显示响应对象的其他属性
                if hasattr(response_delta, '__dict__'):
                    attrs = {k: v for k, v in response_delta.__dict__.items() 
                            if not k.startswith('_') and v is not None}
                    if attrs:
                        print(f"   属性: {json.dumps(attrs, default=str, ensure_ascii=False)[:100]}...")
            else:
                # 简洁模式：只显示内容预览
                preview = content.replace('\n', '\\n').replace('\r', '\\r')
                if len(preview) > 50:
                    preview = preview[:47] + "..."
                print(f"   内容: {preview}")
            
            # 特殊内容标记
            if '\n' in content:
                print(f"   🔄 包含换行符")
            if any(char in content for char in ['。', '！', '？', '.', '!', '?']):
                print(f"   📝 包含句子结束符")
                
        else:
            # 没有内容的 chunk（可能是元数据或控制信息）
            print(f"📦 Chunk #{current_chunk:03d} | 无内容 | 类型: {type(response_delta).__name__}")
            
            if self.verbose and hasattr(response_delta, '__dict__'):
                attrs = {k: v for k, v in response_delta.__dict__.items() 
                        if not k.startswith('_') and v is not None}
                if attrs:
                    print(f"   元数据: {json.dumps(attrs, default=str, ensure_ascii=False)[:100]}...")
        
        print(flush=True)
    
    def end_stream(self):
        """结束流式响应调试"""
        if not self.enabled or self.start_time is None:
            return
            
        duration = time.time() - self.start_time
        
        print("=" * 60)
        print(f"✅ 流式响应完成 - {time.strftime('%H:%M:%S')}")
        print(f"📊 统计信息:")
        print(f"   • 总 chunk 数: {self.chunk_count}")
        print(f"   • 总内容长度: {self.total_content_length} 字符")
        print(f"   • 耗时: {duration:.2f} 秒")
        if self.chunk_count > 0:
            print(f"   • 平均 chunk 大小: {self.total_content_length / self.chunk_count:.1f} 字符")
            print(f"   • 平均 chunk 间隔: {duration / self.chunk_count * 1000:.1f} 毫秒")
        print()
    
    def _extract_content(self, response_delta: Any) -> str:
        """从响应对象中提取内容"""
        # 尝试多种可能的内容属性
        content_attrs = [
            'content',
            'text', 
            'message',
            'data'
        ]
        
        for attr in content_attrs:
            if hasattr(response_delta, attr):
                value = getattr(response_delta, attr)
                if isinstance(value, str) and value:
                    return value
        
        # 尝试 delta 结构
        if hasattr(response_delta, 'delta'):
            delta = response_delta.delta
            for attr in content_attrs:
                if hasattr(delta, attr):
                    value = getattr(delta, attr)
                    if isinstance(value, str) and value:
                        return value
        
        # 尝试 choices 结构（OpenAI 格式）
        if hasattr(response_delta, 'choices') and response_delta.choices:
            choice = response_delta.choices[0]
            if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                content = choice.delta.content
                if isinstance(content, str) and content:
                    return content
        
        return ""

# 全局调试器实例
stream_debugger = StreamDebugger(enabled=True, verbose=False)

def enable_stream_debug(verbose: bool = False):
    """启用流式响应调试"""
    global stream_debugger
    stream_debugger.enabled = True
    stream_debugger.verbose = verbose
    print("✅ 流式响应调试已启用" + (" (详细模式)" if verbose else " (简洁模式)"))

def disable_stream_debug():
    """禁用流式响应调试"""
    global stream_debugger
    stream_debugger.enabled = False
    print("❌ 流式响应调试已禁用")

def log_stream_chunk(response_delta: Any, model_name: str = "Unknown", chunk_index: Optional[int] = None):
    """记录流式响应 chunk（便捷函数）"""
    global stream_debugger
    
    # 如果是第一个 chunk，自动开始调试
    if stream_debugger.chunk_count == 0:
        stream_debugger.start_stream(model_name)
    
    stream_debugger.log_chunk(response_delta, chunk_index)

def finish_stream_debug():
    """完成流式响应调试（便捷函数）"""
    global stream_debugger
    stream_debugger.end_stream()
