/**
 * PDA 硬件扫描驱动 (Honeywell/Zebra Android 广播模式)
 */
export const PDA_SCAN_ACTION = 'com.honeywell.scan.broadcast';
export const PDA_SCAN_DATA_KEY = 'data';

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
        filter.addAction(PDA_SCAN_ACTION);

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
