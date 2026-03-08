import React from 'react';
import { View, Text, StyleSheet, Button, TouchableOpacity } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function ScannerScreen({ navigation }) {
    const [permission, requestPermission] = useCameraPermissions();

    if (!permission) {
        return <View style={styles.container} />;
    }

    if (!permission.granted) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.permissionText}>需要您的相机权限才能扫描资产标签</Text>
                <Button onPress={requestPermission} title="授权相机" />
            </View>
        );
    }

    const handleBarcodeScanned = async ({ type, data }) => {
        let token = data;
        if (data.includes('/asset/')) {
            const parts = data.split('/asset/');
            token = parts[parts.length - 1];
        } else if (data.includes('http')) {
            // Not a valid token but we attempt navigation so the Detail screen can show error
            token = data;
        }

        // Navigate to detail page
        navigation.navigate('资产详情', { token });
    };

    return (
        <View style={styles.container}>
            <View style={styles.cameraContainer}>
                <Text style={styles.cameraTitle}>将资产二维码放入扫描框</Text>

                <CameraView
                    style={styles.camera}
                    facing="back"
                    onBarcodeScanned={handleBarcodeScanned}
                    barcodeScannerSettings={{
                        barcodeTypes: ["qr"],
                    }}
                >
                    <View style={styles.overlay}>
                        <View style={styles.scannerBox}>
                            <View style={[styles.corner, styles.topLeft]} />
                            <View style={[styles.corner, styles.topRight]} />
                            <View style={[styles.corner, styles.bottomLeft]} />
                            <View style={[styles.corner, styles.bottomRight]} />
                        </View>
                    </View>
                </CameraView>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        padding: 20
    },
    permissionText: {
        textAlign: 'center',
        marginBottom: 20,
        fontSize: 16
    },
    cameraContainer: {
        flex: 1,
    },
    cameraTitle: {
        color: '#fff',
        textAlign: 'center',
        padding: 40,
        paddingTop: 60,
        fontSize: 18,
        fontWeight: 'bold',
        zIndex: 10,
        position: 'absolute',
        top: 0,
        width: '100%',
        backgroundColor: 'rgba(0,0,0,0.4)'
    },
    camera: {
        flex: 1,
    },
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'center',
        alignItems: 'center'
    },
    scannerBox: {
        width: 250,
        height: 250,
        backgroundColor: 'transparent',
        justifyContent: 'center',
        alignItems: 'center'
    },
    corner: {
        position: 'absolute',
        width: 40,
        height: 40,
        borderColor: '#4f46e5',
    },
    topLeft: {
        top: 0,
        left: 0,
        borderTopWidth: 4,
        borderLeftWidth: 4,
    },
    topRight: {
        top: 0,
        right: 0,
        borderTopWidth: 4,
        borderRightWidth: 4,
    },
    bottomLeft: {
        bottom: 0,
        left: 0,
        borderBottomWidth: 4,
        borderLeftWidth: 4,
    },
    bottomRight: {
        bottom: 0,
        right: 0,
        borderBottomWidth: 4,
        borderRightWidth: 4,
    }
});
