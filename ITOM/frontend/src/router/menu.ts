export interface MenuItem {
    title: string;
    icon: string;
    path: string;
    showInMobile?: boolean; // 是否在移动端九宫格展示
    children?: MenuItem[];
}

export const menuConfig: MenuItem[] = [
    {
        title: '控制台概览',
        icon: 'Odometer',
        path: '/dashboard',
        showInMobile: true
    },
    {
        title: '资产管理',
        icon: 'Box',
        path: '/assets',
        showInMobile: true,
        children: [
            { title: '资产台账总览', icon: 'Memo', path: '/assets/list', showInMobile: true },
            { title: '资产分类字典', icon: 'Files', path: '/assets/categories', showInMobile: true }
        ]
    },
    {
        title: '域（AD）管理',
        icon: 'UserFilled',
        path: '/ad',
        showInMobile: true,
        children: [
            { title: '域用户开通向导', icon: 'Connection', path: '/ad/provision', showInMobile: true },
            { title: '域用户检索', icon: 'Search', path: '/ad/users', showInMobile: true },
            { title: '安全组策略', icon: 'Lock', path: '/ad/groups', showInMobile: true }
        ]
    },
    {
        title: '系统配置',
        icon: 'Setting',
        path: '/settings',
        showInMobile: true,
        children: [
            { title: '系统底座配置', icon: 'Cpu', path: '/settings/system', showInMobile: true },
            { title: '命名规范中心', icon: 'Collection', path: '/settings/rules', showInMobile: true },
            { title: '权限模板配置', icon: 'List', path: '/settings/templates', showInMobile: true },
            { title: '标签打印模板', icon: 'Printer', path: '/settings/printer', showInMobile: false }
        ]
    }
]
