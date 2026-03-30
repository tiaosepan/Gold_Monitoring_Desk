# 使用curl测试API性能（排除requests库影响）

Write-Host "======================================================================"
Write-Host "API性能测试 - 使用curl (非Python requests)"
Write-Host "======================================================================"
Write-Host ""

$endpoints = @(
    @{Path="/api/ping"; Name="Ping端点"},
    @{Path="/api/db_test"; Name="单次查询"},
    @{Path="/api/status"; Name="系统状态"}
)

foreach ($endpoint in $endpoints) {
    Write-Host "$($endpoint.Name) ($($endpoint.Path))"
    Write-Host "----------------------------------------------------------------------"
    
    $times = @()
    for ($i = 1; $i -le 5; $i++) {
        $start = Get-Date
        curl -s "http://localhost:8000$($endpoint.Path)" > $null
        $elapsed = ((Get-Date) - $start).TotalMilliseconds
        $times += $elapsed
        Write-Host "  请求$i : $($elapsed.ToString('0'))ms"
    }
    
    $avg = ($times | Measure-Object -Average).Average
    $p95 = ($times | Sort-Object)[([Math]::Ceiling($times.Count * 0.95) - 1)]
    
    Write-Host "  平均: $($avg.ToString('0'))ms"
    Write-Host "  P95: $($p95.ToString('0'))ms"
    Write-Host ""
}

Write-Host "======================================================================"
Write-Host "如果curl很快 -> requests库配置问题"
Write-Host "如果curl也慢 -> 服务器配置问题"
Write-Host "======================================================================"
