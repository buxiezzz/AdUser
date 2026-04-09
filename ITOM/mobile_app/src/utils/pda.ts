/**
 * PDA 硬件扫描驱动 (Honeywell/Zebra Android 广播模式)
 */
const PDA_ACTIONS = [
    'com.honeywell.scan.broadcast',        // Honeywell
    'com.symbol.datawedge.api.RESULT_ACTION',// Zebra
    'com.android.serial.BARCODE_DATA_ACTION', // 通用/新大陆
    'dw.ex.scanner.read',                   // 其它
];
export const PDA_SCAN_DATA_KEY = 'data'; // 绝大多数 PDA 默认数据键为 data 或 value

let main: any = null;
let receiver: any = null;
let filter: any = null;

/**
 * 开启 PDA 广播监听
 * @param callback 扫码结果回调
 */
export function startPDAListener(callback: (code: string) => void) {
    // #ifdef APP-PLUS
    if (plus.os.name !== 'Android') return;

    try {
        main = plus.android.runtimeMainActivity();
        plus.android.importClass('android.content.IntentFilter');
        filter = plus.android.newObject('android.content.IntentFilter');
        
        // 批量添加常见的 PDA 广播动作，提高兼容性
        PDA_ACTIONS.forEach(action => {
            filter.addAction(action);
        });

        // 创建广播接收器
        receiver = plus.android.implements('io.dcloud.feature.internal.reflect.BroadcastReceiver', {
            onReceive: function(context: any, intent: any) {
                plus.android.importClass(intent);
                const code = intent.getStringExtra(PDA_SCAN_DATA_KEY);
                if (code) {
                    console.log('[PDA] 扫码成功:', code);
                    callback(code);
                }
            }
        });

        main.registerReceiver(receiver, filter);
        console.log('[PDA] 扫码监听已启动');
    } catch (e) {
        console.error('[PDA] 监听启动失败:', e);
    }
    // #endif
}

/**
 * 停止 PDA 广播监听
 */
export function stopPDAListener() {
    // #ifdef APP-PLUS
    if (main && receiver) {
        try {
            main.unregisterReceiver(receiver);
            console.log('[PDA] 扫码监听已注销');
        } catch (e) {
            console.error('[PDA] 注销失败:', e);
        }
        receiver = null;
    }
    // #endif
}
