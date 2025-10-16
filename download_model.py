"""
预下载嵌入模型脚本
Pre-download embedding model script
"""
import os

# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("=" * 60)
print("开始下载嵌入模型 (Downloading embedding model)...")
print("模型: sentence-transformers/all-MiniLM-L6-v2")
print("大小: ~90MB")
print("=" * 60)

try:
    from sentence_transformers import SentenceTransformer

    print("\n[1/2] 正在下载模型...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("[2/2] 测试模型...")
    # 测试模型
    test_embedding = model.encode("Hello world")
    print(f"      嵌入向量维度: {len(test_embedding)}")

    print("\n" + "=" * 60)
    print("✓ 模型下载成功！")
    print("✓ 模型已缓存到本地")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ 下载失败: {e}")
    print("\n可能的解决方案:")
    print("1. 检查网络连接")
    print("2. 尝试使用 VPN")
    print("3. 手动设置代理")
    exit(1)
