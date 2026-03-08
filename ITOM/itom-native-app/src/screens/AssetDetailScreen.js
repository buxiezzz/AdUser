import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import api from '../api/axios';

export default function AssetDetailScreen({ route, navigation }) {
    const { token } = route.params;
    const [assetDetails, setAssetDetails] = useState(null);
    const [fetching, setFetching] = useState(true);
    const [errorMsg, setErrorMsg] = useState('');

    const fetchAsset = async () => {
        setFetching(true);
        setErrorMsg('');
        try {
            const res = await api.get(`/api/assets/mobile/${token}`);
            setAssetDetails(res.data);
        } catch (e) {
            setErrorMsg(e.response?.data?.detail || '未找到该资产信息或无权限');
            setAssetDetails(null);
        } finally {
            setFetching(false);
        }
    };

    useEffect(() => {
        fetchAsset();
    }, [token]);

    const handleReturn = () => {
        Alert.alert('确认', '确定要将该设备强制退库吗？', [
            { text: '取消', style: 'cancel' },
            {
                text: '强制退库',
                style: 'destructive',
                onPress: async () => {
                    try {
                        const res = await api.patch(`/api/assets/${assetDetails.id}/status`, { status: "在库" });
                        setAssetDetails(res.data);
                        Alert.alert('成功', '设备已退回主仓库');
                    } catch (e) {
                        Alert.alert('失败', '退库操作失败无权限');
                    }
                }
            }
        ]);
    };

    if (fetching) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#4f46e5" />
                <Text style={styles.infoText}>正在查询...</Text>
            </View>
        );
    }

    if (errorMsg || !assetDetails) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.errorIcon}>⚠️</Text>
                <Text style={styles.errorText}>{errorMsg || '加载失败'}</Text>
                <TouchableOpacity style={styles.button} onPress={() => navigation.goBack()}>
                    <Text style={styles.buttonText}>返回上一页</Text>
                </TouchableOpacity>
            </View>
        );
    }

    const dynamics = [];
    if (assetDetails.dynamic_attributes) {
        for (const key in assetDetails.dynamic_attributes) {
            if (assetDetails.dynamic_attributes[key] && key !== '规格型号' && key !== '序列号') {
                dynamics.push({ key, val: assetDetails.dynamic_attributes[key] });
            }
        }
    }

    return (
        <ScrollView style={styles.container}>
            <View style={styles.cardHeader}>
                <Text style={styles.title}>{assetDetails.category?.name || '未知资产'}</Text>
                <Text style={styles.code}>{assetDetails.asset_code}</Text>
                <View style={styles.statusBadge}>
                    <Text style={styles.statusText}>{assetDetails.status}</Text>
                </View>
            </View>

            <View style={styles.card}>
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>归属信息</Text>
                    <View style={styles.row}>
                        <Text style={styles.label}>使用人</Text>
                        <Text style={styles.value}>{assetDetails.owner?.name || '闲置中'}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>所属部门</Text>
                        <Text style={styles.value}>{assetDetails.owner?.department || '-'}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>入管时间</Text>
                        <Text style={styles.value}>{new Date(assetDetails.created_at).toISOString().split('T')[0]}</Text>
                    </View>
                </View>
            </View>

            <View style={styles.card}>
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>主要设备参数</Text>
                    {assetDetails.dynamic_attributes?.['规格型号'] && (
                        <View style={styles.row}>
                            <Text style={styles.label}>型号规格</Text>
                            <Text style={styles.value}>{assetDetails.dynamic_attributes['规格型号']}</Text>
                        </View>
                    )}
                    {assetDetails.dynamic_attributes?.['序列号'] && (
                        <View style={styles.row}>
                            <Text style={styles.label}>S/N (硬件序列号)</Text>
                            <Text style={styles.value}>{assetDetails.dynamic_attributes['序列号']}</Text>
                        </View>
                    )}
                    {dynamics.map(d => (
                        <View style={styles.row} key={d.key}>
                            <Text style={styles.label}>{d.key}</Text>
                            <Text style={styles.value}>{d.val}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {assetDetails.status !== '在库' && (
                <View style={styles.actionContainer}>
                    <TouchableOpacity style={styles.actionButtonDestructive} onPress={handleReturn}>
                        <Text style={styles.actionButtonText}>立刻退库该设备</Text>
                    </TouchableOpacity>
                </View>
            )}

            <View style={{ height: 40 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f3f4f6',
        padding: 16
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20
    },
    infoText: {
        marginTop: 16,
        fontSize: 16,
        color: '#6b7280'
    },
    errorIcon: {
        fontSize: 64,
        marginBottom: 16
    },
    errorText: {
        fontSize: 18,
        color: '#ef4444',
        marginBottom: 30,
        textAlign: 'center'
    },
    button: {
        backgroundColor: '#4f46e5',
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 24
    },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold'
    },
    cardHeader: {
        backgroundColor: '#4f46e5',
        borderRadius: 20,
        padding: 24,
        marginBottom: 16,
        alignItems: 'center',
        shadowColor: '#4f46e5',
        shadowOpacity: 0.3,
        shadowRadius: 10,
        elevation: 5
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#fff',
        marginBottom: 4
    },
    code: {
        fontSize: 14,
        fontFamily: 'Courier',
        color: '#c7d2fe',
        marginBottom: 16
    },
    statusBadge: {
        backgroundColor: '#fff',
        paddingHorizontal: 16,
        paddingVertical: 6,
        borderRadius: 20
    },
    statusText: {
        color: '#4f46e5',
        fontWeight: 'bold',
        fontSize: 14
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 20,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 5,
        elevation: 2
    },
    section: {
        marginBottom: 4
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#4f46e5',
        marginBottom: 16
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#f3f4f6'
    },
    label: {
        color: '#6b7280',
        fontSize: 14
    },
    value: {
        color: '#1f2937',
        fontWeight: 'bold',
        fontSize: 14,
        maxWidth: '70%',
        textAlign: 'right'
    },
    actionContainer: {
        marginTop: 10
    },
    actionButtonDestructive: {
        backgroundColor: '#ef4444',
        padding: 16,
        borderRadius: 16,
        alignItems: 'center',
        shadowColor: '#ef4444',
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4
    },
    actionButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold'
    }
});
