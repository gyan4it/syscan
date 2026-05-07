import sys
sys.path.insert(0, r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository')

from syscan_web.server.ai_engine import AIDeletionEngine

# Initialize AI engine
ai = AIDeletionEngine()

# Test prediction
test_files = [
    (r'C:\Users\Test\node_modules\cache', 2000000000),  # 2GB npm cache
    (r'C:\Users\Test\AppData\Local\Temp\old.log', 500000000),  # 500MB log
    (r'C:\Windows\System32\drivers', 1000000000),  # System file
]

print('AI Engine Predictions:')
print('-' * 60)
for path, size in test_files:
    prob = ai.predict_deletion(path, size)
    recommendation = 'SAFE TO DELETE' if prob > 0.7 else 'REVIEW REQUIRED' if prob > 0.3 else 'KEEP'
    print(f'Path: {path}')
    print(f'  Size: {size / (1024**3):.2f} GB')
    print(f'  Probability: {prob:.2%}')
    print(f'  Recommendation: {recommendation}')
    print()
print('AI Engine working!')
