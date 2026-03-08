import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import api from '../api/axios';

export default function AssetListScreen({ navigation, route }) {
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    // If navigated from Dashboard with a filter
    const initialFilter = route.params?.filter || null;

    const fetchAssets = async () => {
        try {
            const res = await api.get('/api/assets/');
            let data = res.data;
            if (initialFilter) {
                // Approximate client-side filtering logic for the demo
                data = data.filter(a => a.status === initialFilter || (initialFilter === '在用' && a.status === '借用中') || (initialFilter === '闲置' && a.status === '在库'));
            }
            setAssets(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAssets();
    }, [initialFilter]);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchAssets().then(() => setRefreshing(false));
    }, [initialFilter]);

    const filteredAssets = assets.filter(a => {
        if (!search) return true;
        const kw = search.toLowerCase();
        return (
            (a.asset_code && a.asset_code.toLowerCase().includes(kw)) ||
            (a.owner && a.owner.name && a.owner.name.toLowerCase().includes(kw))
        );
    });

    const getStatusStyle = (status) => {
        if (status === '在用' || status === '借用中') return styles.statusGreen;
        if (status === '闲置' || status === '在库') return styles.statusYellow;
        if (status === '维修中') return styles.statusRed;
        return styles.statusGray;
    };

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={styles.card}
            onPress={() => navigation.navigate('资产详情', { token: item.qr_code_token || item.id })}
        >
            <View style={styles.cardHeader}>
                <Text style={styles.cardCategory}>{item.category ? item.category.name : '未知资产'}</Text>
                <View style={[styles.statusBadge, getStatusStyle(item.status)]}>
                    <Text style={styles.statusText}>{item.status}</Text>
                </View>
            </View>
            <Text style={styles.cardCode}>{item.asset_code}</Text>
            <View style={styles.cardInfo}>
                <Text style={styles.cardOwner}>{item.owner ? item.owner.name : '闲置'}</Text>
                <Text style={styles.cardDepartment}>{item.owner ? item.owner.department : '-'}</Text>
            </View>
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            <View style={styles.searchContainer}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="按编码或姓名搜索..."
                    value={search}
                    onChangeText={setSearch}
                    placeholderTextColor="#9ca3af"
                />
            </View>

            {loading ? (
                <View style={styles.center}>
                    <ActivityIndicator size="large" color="#4f46e5" />
                </View>
            ) : (
                <FlatList
                    data={filteredAssets}
                    keyExtractor={(item) => item.id.toString()}
                    renderItem={renderItem}
                    contentContainerStyle={styles.list}
                    refreshing={refreshing}
                    onRefresh={onRefresh}
                    ListEmptyComponent={<Text style={styles.emptyText}>没有找到相关资产</Text>}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f3f4f6',
    },
    searchContainer: {
        padding: 16,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e5e7eb'
    },
    searchInput: {
        backgroundColor: '#f3f4f6',
        borderRadius: 12,
        padding: 12,
        fontSize: 16,
        color: '#1f2937'
    },
    list: {
        padding: 16,
        paddingBottom: 40
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 5,
        elevation: 2
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8
    },
    cardCategory: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1f2937',
    },
    statusBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 10
    },
    statusGreen: { backgroundColor: '#d1fae5' },
    statusYellow: { backgroundColor: '#fef3c7' },
    statusRed: { backgroundColor: '#fee2e2' },
    statusGray: { backgroundColor: '#f3f4f6' },
    statusText: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#374151' // Will override based on context usually, keeping simple here
    },
    cardCode: {
        fontSize: 12,
        color: '#9ca3af',
        fontFamily: 'Courier',
        marginBottom: 16
    },
    cardInfo: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        borderTopWidth: 1,
        borderTopColor: '#f3f4f6',
        paddingTop: 12
    },
    cardOwner: {
        fontWeight: 'bold',
        color: '#4b5563'
    },
    cardDepartment: {
        color: '#9ca3af',
        fontSize: 14
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center'
    },
    emptyText: {
        textAlign: 'center',
        color: '#9ca3af',
        marginTop: 40,
        fontSize: 16
    }
});
