/**
 * 德佟标签打印机 (LPAPI) 桥接 Service
 * 流程：requestBluetoothAuth → startDiscovery（每发现一台设备回调一次）→ 识别打印机 → openPrinter → startJob → draw* → commitJob
 */
import { config as appConfig } from '../config';

function alertModal(title: string, content: string) {
    console.error('[打印机]', title, content);
    uni.showModal({ title, content, showCancel: false });
}

function toast(msg: string, icon: 'none' | 'success' | 'error' = 'none', duration = 2500) {
    console.log('[打印机]', msg);
    uni.showToast({ title: msg, icon, duration });
}

/** 执行打印排版并提交 */
function doPrint(lpapi: any, asset: any, templateConfig: any) {
    try {
        const paper = templateConfig.paper || { width: 70, height: 50, orientation: 0, gapType: 2, darkness: 8, speed: 2 };
        const elements = templateConfig.elements || [];

        lpapi.startJob({ width: paper.width, height: paper.height, orientation: paper.orientation });

        // APP-PLUS 环境下没有 window.location，从 appConfig.baseUrl 提取服务器根地址
        const serverRoot = appConfig.baseUrl.replace(/\/api\/?$/, '');
        const qrUrl = asset.qr_code_token ? `${serverRoot}/mobile/asset/${asset.qr_code_token}` : serverRoot;

        for (const item of elements) {
            if (item.type === 'text') {
                // 读取动态字段值或固定文字
                let textValue = item.value || '';
                if (item.field) {
                    textValue = item.field.split('.').reduce((o: any, i: string) => (o ? o[i] : ''), asset) || '-';
                }
                const finalStr = `${item.prefix || ''}${textValue}`;
                lpapi.drawText({
                    text: finalStr,
                    x: item.x,
                    y: item.y,
                    fontHeight: item.fontHeight,
                    width: item.width,
                    height: item.height
                });
            } else if (item.type === 'qrcode') {
                if (typeof lpapi.draw2DQRCode === 'function') {
                    lpapi.draw2DQRCode({ text: qrUrl, x: item.x, y: item.y, width: item.width });
                }
            } else if (item.type === 'line') {
                if (typeof lpapi.drawLine === 'function') {
                    // lineWidth 作为线宽，width 和 height 代表水平和垂直的偏移长度
                    lpapi.drawLine({ 
                        x1: item.x, 
                        y1: item.y, 
                        x2: item.x + (item.width || 0), 
                        y2: item.y + (item.height || 0), 
                        lineWidth: item.lineWidth || 0.5 
                    });
                }
            } else if (item.type === 'rect') {
                if (typeof lpapi.drawRectangle === 'function') {
                    lpapi.drawRectangle({ x: item.x, y: item.y, width: item.width, height: item.height, lineWidth: item.lineWidth || 0.5 });
                } else if (typeof lpapi.drawRect === 'function') {
                    lpapi.drawRect({ x: item.x, y: item.y, width: item.width, height: item.height, lineWidth: item.lineWidth || 0.5 });
                } else if (typeof lpapi.drawLine === 'function') {
                    // 降级使用四条线绘制矩形
                    const lw = item.lineWidth || 0.5;
                    lpapi.drawLine({ x1: item.x, y1: item.y, x2: item.x + item.width, y2: item.y, lineWidth: lw });
                    lpapi.drawLine({ x1: item.x, y1: item.y + item.height, x2: item.x + item.width, y2: item.y + item.height, lineWidth: lw });
                    lpapi.drawLine({ x1: item.x, y1: item.y, x2: item.x, y2: item.y + item.height, lineWidth: lw });
                    lpapi.drawLine({ x1: item.x + item.width, y1: item.y, x2: item.x + item.width, y2: item.y + item.height, lineWidth: lw });
                }
            }
        }

        lpapi.commitJob({ GAP_TYPE: paper.gapType, PRINT_DARKNESS: paper.darkness, PRINT_SPEED: paper.speed }, () => {
            toast('打印成功！', 'success');
            setTimeout(() => { try { lpapi.closePrinter(); } catch (e) {} }, 1500);
        }, (e: any) => {
            alertModal('打印提交失败', JSON.stringify(e));
        });
    } catch (e: any) {
        alertModal('打印排版失败', e?.message || String(e));
    }
}

/** 连接打印机并打印 */
function connectAndPrint(lpapi: any, printerName: string, asset: any, templateConfig: any) {
    console.log('[打印机] 连接设备：', printerName);
    toast(`正在连接：${printerName}`, 'none', 5000);

    lpapi.openPrinter(printerName, (res: any) => {
        console.log('[打印机] openPrinter 成功：', JSON.stringify(res));
        toast('已连接，正在打印...', 'none', 3000);
        setTimeout(() => doPrint(lpapi, asset, templateConfig), 1000);
    }, (err: any) => {
        console.error('[打印机] openPrinter 失败：', JSON.stringify(err));
        alertModal('连接失败', `"${printerName}" 连接失败：\n${JSON.stringify(err)}\n\n可尝试关闭打印机蓝牙后重新开启。`);
    });
}

// 缓存模板配置，避免每次都请求
let cachedTemplate: any = null;

export const printAssetLabel = async (asset: any) => {
    if (!asset) { toast('资产数据为空'); return; }

    // #ifdef H5
    window.print();
    // #endif

    // 拉取最新的模板配置
    toast('正在初始化打印引擎...', 'none', 2000);
    try {
        const userToken = uni.getStorageSync('itom_token');
        const res: any = await uni.request({
            url: `${appConfig.baseUrl}/settings/`,
            method: 'GET',
            header: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        if (res && res.statusCode === 200) {
            const data = res.data;
            if (data && data.PRINT_TEMPLATE) {
                cachedTemplate = data.PRINT_TEMPLATE;
            }
        }
    } catch (e) {
        console.error('[打印机] 获取模板配置失败，使用默认配置', e);
    }

    // 默认兜底配置
    if (!cachedTemplate || !cachedTemplate.elements) {
        cachedTemplate = {
            paper: { width: 70, height: 50, orientation: 0, gapType: 2, darkness: 8, speed: 2 },
            elements: [
                { type: 'text', value: '先惠自动化技术有限公司', x: 5, y: 5, fontHeight: 3, width: 42, height: 6 },
                { type: 'text', field: 'asset_code', prefix: '资产编码: ', x: 5, y: 13, fontHeight: 3, width: 42, height: 6 },
                { type: 'text', field: 'category.name', prefix: '名称: ', x: 5, y: 21, fontHeight: 3, width: 42, height: 6 },
                { type: 'text', field: 'dynamic_attributes.规格型号', prefix: '型号: ', x: 5, y: 29, fontHeight: 3, width: 42, height: 6 },
                { type: 'qrcode', field: 'qr_code_token', x: 50, y: 10, width: 18 }
            ]
        };
    }

    // #ifdef APP-PLUS
    let lpapi: any = null;
    try {
        lpapi = uni.requireNativePlugin('DothanTech-LPAPI');
    } catch (e: any) {
        alertModal('插件加载异常', `请使用自定义调试基座。\n${e?.message || e}`);
        return;
    }
    if (!lpapi) {
        alertModal('插件未加载', '请检查 manifest.json 配置。');
        return;
    }

    // 初始化并申请蓝牙权限
    try { lpapi.init({}); } catch (e) {}
    try { lpapi.requestBluetoothAuth(); } catch (e) {}

    let connected = false;

    // ──────────────────────────────────────────────
    // 先检查是否已有已连接的打印机（省去重新搜索）
    // ──────────────────────────────────────────────
    try {
        const isOpened = lpapi.isPrinterOpened();
        console.log('[打印机] isPrinterOpened:', isOpened);
        if (isOpened === true || isOpened === 1 || isOpened === 'true') {
            console.log('[打印机] 打印机已处于连接状态，直接打印');
            toast('打印机已连接，正在排版打印...', 'none', 3000);
            connected = true;
            setTimeout(() => doPrint(lpapi, asset, cachedTemplate), 500);
            return;
        }
    } catch (e) {}

    // 尝试获取已保存的打印机名（之前连接过的）
    const savedName = uni.getStorageSync('lpapi_printer_name');
    if (savedName) {
        console.log('[打印机] 使用已保存的打印机名：', savedName);
        toast(`正在连接已配对设备：${savedName}`, 'none', 5000);
        lpapi.openPrinter(savedName, (res: any) => {
            console.log('[打印机] 已保存设备连接成功');
            connected = true;
            toast('已连接，正在排版打印...', 'none', 3000);
            setTimeout(() => doPrint(lpapi, asset, cachedTemplate), 1000);
        }, (err: any) => {
            console.warn('[打印机] 已保存设备连接失败，开始重新搜索', JSON.stringify(err));
            uni.removeStorageSync('lpapi_printer_name');
            startScan(lpapi, asset, cachedTemplate);
        });
        return;
    }

    startScan(lpapi, asset, cachedTemplate);

    function startScan(lpapi: any, asset: any, templateConfig: any) {
        toast('正在扫描周边蓝牙打印机...', 'none', 15000);
        console.log('[打印机] 开始 startDiscovery...');


        // startDiscovery：每发现一台蓝牙设备时回调一次
        try {
            lpapi.startDiscovery(
                { timeout: 12000, interval: 500 },
                (deviceInfo: any) => {
                    if (connected) return;
                    console.log('[打印机] 发现设备：', JSON.stringify(deviceInfo));

                    // deviceInfo 可能是 {name, address} 或 {printer} 或直接字符串
                    let devName: string = '';
                    if (typeof deviceInfo === 'string') devName = deviceInfo;
                    else if (deviceInfo?.name) devName = deviceInfo.name;
                    else if (deviceInfo?.printer) devName = deviceInfo.printer;
                    else devName = JSON.stringify(deviceInfo);

                    // 记录发现的所有设备（调试用）
                    const history: string[] = uni.getStorageSync('lpapi_discovered') || [];
                    if (!history.includes(devName)) {
                        history.push(devName);
                        uni.setStorageSync('lpapi_discovered', history);
                    }

                    // 判断是否是德佟打印机（匹配常见命名规则）
                    const lower = devName.toLowerCase();
                    const isPrinter = lower.includes('ylf') || lower.includes('yl') ||
                        lower.includes('dt') || lower.includes('detong') ||
                        lower.includes('dothan') || lower.includes('label') ||
                        lower.includes('printer') || lower.includes('lp') ||
                        lower.includes('print');

                    if (isPrinter) {
                        console.log('[打印机] ✅ 识别为打印机：', devName);
                        connected = true;
                        try { lpapi.stopDiscovery({}); } catch (e) {}
                        uni.setStorageSync('lpapi_printer_name', devName); // 保存以备下次直连
                        connectAndPrint(lpapi, devName, asset, templateConfig);
                    } else {
                        console.log('[打印机] ⬜ 非打印机设备，跳过：', devName);
                    }
                }
            );
        } catch (e: any) {
            alertModal('扫描启动失败', `startDiscovery 异常：${e?.message || e}`);
            return;
        }

        // 12秒后若仍未找到，列出发现的所有设备让用户选
        setTimeout(() => {
            if (connected) return;
            try { lpapi.stopDiscovery({}); } catch (e) {}

            const discovered: string[] = uni.getStorageSync('lpapi_discovered') || [];
            uni.removeStorageSync('lpapi_discovered');
            console.log('[打印机] 扫描结束，发现设备列表：', discovered);

            if (discovered.length === 0) {
                alertModal(
                    '未发现任何蓝牙设备',
                    '扫描12秒后未发现任何设备。\n\n请检查：\n1. 打印机已开机（指示灯闪烁）\n2. 手机蓝牙和定位已开启\n3. 打印机距手机1米内\n4. 已在手机系统蓝牙中配对过该设备'
                );
            } else {
                // 列出所有发现的设备，引导用户
                const deviceListStr = discovered.map((n, i) => `${i + 1}. ${n}`).join('\n');
                uni.showModal({
                    title: `发现 ${discovered.length} 台设备`,
                    content: `扫描未自动识别打印机。\n发现的设备：\n${deviceListStr}\n\n如果您的打印机在列表中，请记住编号告知开发者。`,
                    showCancel: discovered.length > 0,
                    confirmText: discovered.length > 0 ? '连接第1台' : '确定',
                    success: (res) => {
                        if (res.confirm && discovered.length > 0) {
                            const name = discovered[0];
                            uni.setStorageSync('lpapi_printer_name', name);
                            connectAndPrint(lpapi, name, asset, templateConfig);
                        }
                    }
                });
            }
        }, 12500);
    }
    // #endif
};
