# FRED API密钥配置脚本
# 功能: 将FRED API密钥永久保存到系统环境变量

$ApiKey = "38b7f7dc5b334dfea2c32abdac59232f"

Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host "FRED API密钥配置"
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# 设置用户级环境变量（永久有效）
[System.Environment]::SetEnvironmentVariable("FRED_API_KEY", $ApiKey, "User")

Write-Host "[OK] FRED_API_KEY已设置为用户环境变量"
Write-Host "    密钥: $($ApiKey.Substring(0,8))...$($ApiKey.Substring($ApiKey.Length-8))"
Write-Host ""

# 同时设置当前会话
$env:FRED_API_KEY = $ApiKey
Write-Host "[OK] 当前会话环境变量已更新"
Write-Host ""

Write-Host "验证配置..."
Write-Host "    读取环境变量: $env:FRED_API_KEY"
Write-Host ""

Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host "[成功] FRED API密钥配置完成！"
Write-Host ""
Write-Host "说明:"
Write-Host "  - 密钥已永久保存到系统（用户级）"
Write-Host "  - 重启PowerShell后自动生效"
Write-Host "  - 当前会话立即可用"
Write-Host ""
Write-Host "测试API:"
Write-Host "  python scripts\utils\test_fred_api.py"
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
