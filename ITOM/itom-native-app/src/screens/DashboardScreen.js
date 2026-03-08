import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import api from '../api/axios';

export default function DashboardScreen({ navigation }) {
    const [stats, setStats] = useState({ total: 0, active: 0, idle: 0, maintenance: 0 });
    const [refreshing, setRefreshing] = useState(false);

    const fetchStats = async () => {
        try {
            // Simplified fetch just getting the list to derive stats in real app we'd have a stats endpoint
            const res = await api.get('/api/assets/');
            const assets = res.data;
            let active = 0;
            let idle = 0;
            let maintenance = 0;

            assets.forEach(a => {
                if (a.status === '在用' || a.status === '借用中') active++;
                else if (a.status === '闲置' || a.status === '在库') idle++;
                else if (a.status === '维修中') maintenance++;
            });

            setStats({
                total: assets.length,
                active,
                idle,
                maintenance
            });
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchStats().then(() => setRefreshing(false));
    }, []);

    const navigateToList = (filter) => {
        navigation.navigate('清单', { filter });
    };

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            <View style={styles.header}>
                <Text style={styles.title}>工作台</Text>
                <Text style={styles.subtitle}>您的资产总览</Text>
            </View>

            <View style={styles.statsGrid}>
                <TouchableOpacity style={[styles.statCard, styles.bgTotal]} onPress={() => navigateToList(null)}>
                    <Text style={styles.statValue}>{stats.total}</Text>
                    <Text style={styles.statLabel}>总资产</Text>
                </TouchableOpacity>

                <TouchableOpacity style={[styles.statCard, styles.bgActive]} onPress={() => navigateToList('在用')}>
                    <Text style={styles.statValue}>{stats.active}</Text>
                    <Text style={styles.statLabel}>在用设备</Text>
                </TouchableOpacity>

                <TouchableOpacity style={[styles.statCard, styles.bgIdle]} onPress={() => navigateToList('闲置')}>
                    <Text style={styles.statValue}>{stats.idle}</Text>
                    <Text style={styles.statLabel}>闲置在库</Text>
                </TouchableOpacity>

                <TouchableOpacity style={[styles.statCard, styles.bgMaintenance]} onPress={() => navigateToList('维修中')}>
                    <Text style={styles.statValue}>{stats.maintenance}</Text>
                    <Text style={styles.statLabel}>维修中</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.section}>
                <Text style={styles.sectionTitle}>快捷操作</Text>
                <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('扫码')}>
                    <Text style={styles.actionTitle}>📷 扫描资产标签</Text>
                    <Text style={styles.actionSubtitle}>调起相机极速盘点或修改归属</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f3f4f6',
        padding: 16
    },
    header: {
        marginTop: 40,
        marginBottom: 24,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#1f2937'
    },
    subtitle: {
        fontSize: 16,
        color: '#6b7280',
        marginTop: 4
    },
    statsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        marginBottom: 30
    },
    statCard: {
        width: '48%',
        padding: 24,
        borderRadius: 20,
        marginBottom: 16,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOpacity: 0.1,
        shadowRadius: 10,
        elevation: 3
    },
    bgTotal: { backgroundColor: '#4f46e5' },
    bgActive: { backgroundColor: '#10b981' },
    bgIdle: { backgroundColor: '#f59e0b' },
    bgMaintenance: { backgroundColor: '#ef4444' },
    statValue: {
        fontSize: 36,
        fontWeight: 'bold',
        color: '#fff',
        marginBottom: 8
    },
    statLabel: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.8)',
        fontWeight: '600'
    },
    section: {
        marginBottom: 40
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#374151',
        marginBottom: 16
    },
    actionCard: {
        backgroundColor: '#fff',
        padding: 24,
        borderRadius: 20,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 10,
        elevation: 2
    },
    actionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: 8
    },
    actionSubtitle: {
        fontSize: 14,
        color: '#6b7280'
    }
});
