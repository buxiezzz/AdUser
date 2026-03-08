import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ActivityIndicator, View, TouchableOpacity, Text } from 'react-native';

import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import AssetListScreen from './src/screens/AssetListScreen';
import ScannerScreen from './src/screens/ScannerScreen';
import AssetDetailScreen from './src/screens/AssetDetailScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{
      tabBarActiveTintColor: '#4f46e5',
      headerShown: false
    }}>
      <Tab.Screen
        name="工作台"
        component={DashboardScreen}
        options={{
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📊</Text>
        }}
      />
      <Tab.Screen
        name="清单"
        component={AssetListScreen}
        options={{
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📝</Text>
        }}
      />
      <Tab.Screen
        name="扫码"
        component={ScannerScreen}
        options={{
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📷</Text>
        }}
      />
    </Tab.Navigator>
  );
}

import { AuthContext } from './src/context/AuthContext';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token
    const checkToken = async () => {
      try {
        const token = await AsyncStorage.getItem('utom_token');
        if (token) {
          setIsAuthenticated(true);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    checkToken();
  }, []);

  const handleLogout = async () => {
    await AsyncStorage.removeItem('utom_token');
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#4f46e5" />
      </View>
    );
  }

  return (
    <AuthContext.Provider value={{ setIsAuthenticated }}>
      <NavigationContainer>
        <Stack.Navigator>
          {!isAuthenticated ? (
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              options={{ headerShown: false }}
            />
          ) : (
            <>
              <Stack.Screen
                name="MainTabs"
                component={MainTabs}
                options={{
                  title: 'ITOM 管理系统',
                  headerRight: () => (
                    <TouchableOpacity onPress={handleLogout} style={{ marginRight: 10, padding: 5 }}>
                      <Text style={{ color: '#ef4444', fontWeight: 'bold' }}>退出</Text>
                    </TouchableOpacity>
                  )
                }}
              />
              <Stack.Screen
                name="资产详情"
                component={AssetDetailScreen}
                options={{
                  presentation: 'modal',
                  headerBackTitle: '返回'
                }}
              />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </AuthContext.Provider>
  );
}
