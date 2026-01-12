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
	import Logs from '$lib/components/icons/Logs.svelte';
	import LogsList from '$lib/components/logs/LogsList.svelte';
	import LogsCreate from '$lib/components/logs/LogsCreate.svelte';
	import ManagementDashboardButton from '$lib/components/chat/ManagementDashboardButton.svelte';

	import { getGroupsWithLogs, getProblemCategories, getEquipmentGroups } from '$lib/apis/logs';

	let selectedTab = 'view';

	// Data loaded on mount
	let availableGroups = [];
	let problemCategories = [];
	let availableEquipment = [];

	// Track selected group for filtering logs
	let selectedGroupId = '';

	// Get tab from URL query parameter, default to 'view'
	$: {
		const tabFromUrl = $page.url.searchParams.get('tab');
		if (tabFromUrl === 'create' || tabFromUrl === 'view') {
			selectedTab = tabFromUrl;
		} else {
			selectedTab = 'view';
		}
	}

	const loadInitialData = async () => {
		try {
			// Load groups with database configured
			const groupsResponse = await getGroupsWithLogs(localStorage.token);
			if (groupsResponse) {
				availableGroups = groupsResponse;
			}

			// Load problem categories
			const categoriesResponse = await getProblemCategories(localStorage.token);
			if (categoriesResponse) {
				problemCategories = categoriesResponse;
			}

			// Load equipment groups
			const equipmentResponse = await getEquipmentGroups(localStorage.token);
			if (equipmentResponse) {
				availableEquipment = equipmentResponse;
			}
		} catch (error) {
			console.error('Error loading initial data:', error);
			toast.error($i18n.t('Error loading logs data'));
		}
	};

	const changeTab = (tab) => {
		goto(`/logs?tab=${tab}`);
	};

	onMount(async () => {
		loadInitialData();
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
						<Logs className="size-5" strokeWidth="2" />
						<div class="text-lg font-medium">{$i18n.t('Logs')}</div>
					</div>

					<div class="self-center flex items-center gap-1">
						<ManagementDashboardButton />

						{#if $user !== undefined && $user !== null}
							<UserMenu
								className="max-w-[240px]"
								role={$user?.role}
								help={true}
							>
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
			<div class="max-w-6xl mx-auto px-4 py-6">
				<!-- Tab Navigation -->
				<div class="flex border-b border-gray-200 dark:border-gray-700 mb-6">
					<button
						class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'view'
							? 'border-blue-500 text-blue-600 dark:text-blue-400'
							: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
						on:click={() => changeTab('view')}
					>
						{$i18n.t('View Logs')}
					</button>

					{#if availableGroups.length > 0}
						<button
							class="px-4 py-2 text-sm font-medium border-b-2 {selectedTab === 'create'
								? 'border-blue-500 text-blue-600 dark:text-blue-400'
								: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
							on:click={() => changeTab('create')}
						>
							{$i18n.t('Create Log')}
						</button>
					{/if}
				</div>

				<!-- Tab Content -->
				{#if selectedTab === 'view'}
					<LogsList bind:selectedGroupId {availableGroups} />
				{:else if selectedTab === 'create'}
					<LogsCreate
						{availableGroups}
						{problemCategories}
						{availableEquipment}
						on:log-created={() => changeTab('view')}
					/>
				{/if}
			</div>
		</div>
	</div>
