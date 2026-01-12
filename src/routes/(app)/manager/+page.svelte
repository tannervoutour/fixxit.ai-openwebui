<script>
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import PendingUsersTab from '$lib/components/manager/PendingUsersTab.svelte';
	import InvitationsTab from '$lib/components/manager/InvitationsTab.svelte';
	import GroupMembersTab from '$lib/components/manager/GroupMembersTab.svelte';
	import ManagementDashboardButton from '$lib/components/chat/ManagementDashboardButton.svelte';

	import { getMyManagedGroups } from '$lib/apis/managers';

	let selectedTab = 'pending';
	let managedGroups = [];
	let loading = true;

	// Redirect if not manager or admin
	$: if ($user && $user.role !== 'manager' && $user.role !== 'admin') {
		toast.error($i18n.t('Access denied. Manager role required.'));
		goto('/');
	}

	// Get tab from URL query parameter
	$: {
		const tabFromUrl = $page.url.searchParams.get('tab');
		if (tabFromUrl && ['pending', 'invitations', 'members'].includes(tabFromUrl)) {
			selectedTab = tabFromUrl;
		}
	}

	const changeTab = (tab) => {
		goto(`/manager?tab=${tab}`);
	};

	const loadManagedGroups = async () => {
		try {
			loading = true;
			const response = await getMyManagedGroups(localStorage.token);
			if (response && response.groups) {
				managedGroups = response.groups;
			}
		} catch (error) {
			console.error('Error loading managed groups:', error);
			toast.error($i18n.t('Error loading groups'));
		} finally {
			loading = false;
		}
	};

	onMount(async () => {
		await loadManagedGroups();
	});
</script>

<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''} max-w-full"
>
	<!-- Top Navigation Bar -->
	<nav class="px-2 pt-1.5 backdrop-blur-xl w-full drag-region">
		<div class="flex items-center">
			{#if $mobile}
				<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							id="sidebar-toggle-button"
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							on:click={() => {
								showSidebar.set(!$showSidebar);
							}}
						>
							<div class="self-center p-1.5">
								<Sidebar />
							</div>
						</button>
					</Tooltip>
				</div>
			{/if}

			<div class="ml-2 py-0.5 self-center flex items-center justify-between w-full">
				<div class="flex items-center gap-2">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="size-5"
					>
						<path
							d="M4.5 6.375a4.125 4.125 0 1 1 8.25 0 4.125 4.125 0 0 1-8.25 0ZM14.25 8.625a3.375 3.375 0 1 1 6.75 0 3.375 3.375 0 0 1-6.75 0ZM1.5 19.125a7.125 7.125 0 0 1 14.25 0v.003l-.001.119a.75.75 0 0 1-.363.63 13.067 13.067 0 0 1-6.761 1.873c-2.472 0-4.786-.684-6.76-1.873a.75.75 0 0 1-.364-.63l-.001-.122ZM17.25 19.128l-.001.144a2.25 2.25 0 0 1-.233.96 10.088 10.088 0 0 0 5.06-1.01.75.75 0 0 0 .42-.643 4.875 4.875 0 0 0-6.957-4.611 8.586 8.586 0 0 1 1.71 5.157v.003Z"
						/>
					</svg>
					<div class="text-lg font-medium">{$i18n.t('User Management')}</div>
				</div>

				<div class="self-center flex items-center gap-1">
					<ManagementDashboardButton />

					{#if $user !== undefined && $user !== null}
						<UserMenu className="max-w-[240px]" role={$user?.role} help={true}>
							<button
								class="select-none flex rounded-xl p-1.5 w-full hover:bg-gray-50 dark:hover:bg-gray-850 transition"
								aria-label="User Menu"
							>
								<div class="self-center">
									<img
										src={`${WEBUI_API_BASE_URL}/users/${$user?.id}/profile/image`}
										class="size-6 object-cover rounded-full"
										alt="User profile"
										draggable="false"
									/>
								</div>
							</button>
						</UserMenu>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<!-- Main Content Area -->
	<div class="pb-1 flex-1 max-h-full overflow-y-auto @container">
		<div class="max-w-7xl mx-auto px-4 py-6">
			<!-- Groups Info Banner -->
			{#if !loading}
				<div class="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
					<div class="flex items-center justify-between">
						<div>
							<h3 class="font-medium text-gray-900 dark:text-gray-100">
								{$i18n.t('Managing')} {managedGroups.length}
								{managedGroups.length === 1 ? $i18n.t('Group') : $i18n.t('Groups')}
							</h3>
							<p class="text-sm text-gray-600 dark:text-gray-400">
								{managedGroups.map((g) => g.name).join(', ')}
							</p>
						</div>
						<div class="text-right">
							<div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
								{managedGroups.reduce((sum, g) => sum + g.member_count, 0)}
							</div>
							<div class="text-xs text-gray-600 dark:text-gray-400">
								{$i18n.t('Total Members')}
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Tab Navigation -->
			<div class="flex border-b border-gray-200 dark:border-gray-700 mb-6">
				<button
					class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'pending'
						? 'border-blue-500 text-blue-600 dark:text-blue-400'
						: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
					on:click={() => changeTab('pending')}
				>
					{$i18n.t('Pending Users')}
				</button>

				<button
					class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'invitations'
						? 'border-blue-500 text-blue-600 dark:text-blue-400'
						: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
					on:click={() => changeTab('invitations')}
				>
					{$i18n.t('Invitation Links')}
				</button>

				<button
					class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'members'
						? 'border-blue-500 text-blue-600 dark:text-blue-400'
						: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
					on:click={() => changeTab('members')}
				>
					{$i18n.t('Group Members')}
				</button>
			</div>

			<!-- Tab Content -->
			{#if !loading}
				{#if selectedTab === 'pending'}
					<PendingUsersTab />
				{:else if selectedTab === 'invitations'}
					<InvitationsTab {managedGroups} />
				{:else if selectedTab === 'members'}
					<GroupMembersTab {managedGroups} />
				{/if}
			{:else}
				<div class="flex justify-center py-12">
					<div class="text-center">
						<div class="animate-spin size-8 border-4 border-gray-300 dark:border-gray-700 border-t-blue-600 rounded-full mx-auto mb-4"></div>
						<p class="text-gray-600 dark:text-gray-400">{$i18n.t('Loading...')}</p>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
