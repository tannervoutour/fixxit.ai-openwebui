<script>
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import { getGroupsWithLogs } from '$lib/apis/logs';
	import { getGroupById } from '$lib/apis/groups';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');

	let availableGroups = [];
	let showDropdown = false;
	let loading = false;

	const loadGroups = async () => {
		console.log('[Management Dashboard] User role:', $user?.role);
		console.log('[Management Dashboard] User managed_groups:', $user?.managed_groups);

		if ($user?.role !== 'manager') {
			console.log('[Management Dashboard] Not a manager, skipping');
			return;
		}

		// Check if user has managed_groups assigned
		if (!$user?.managed_groups || $user.managed_groups.length === 0) {
			console.log('[Management Dashboard] No managed groups assigned to this manager');
			return;
		}

		try {
			loading = true;
			console.log('[Management Dashboard] Loading managed groups...');

			// Fetch details for each managed group
			const groupsWithDashboard = [];
			for (const groupId of $user.managed_groups) {
				try {
					console.log('[Management Dashboard] Fetching group:', groupId);
					const fullGroup = await getGroupById(localStorage.token, groupId);
					console.log('[Management Dashboard] Full group data:', fullGroup);
					console.log('[Management Dashboard] Dashboard URL:', fullGroup?.data?.management_dashboard_url);

					if (fullGroup?.data?.management_dashboard_url) {
						groupsWithDashboard.push({
							id: fullGroup.id,
							name: fullGroup.name,
							dashboardUrl: fullGroup.data.management_dashboard_url
						});
						console.log('[Management Dashboard] Added group with dashboard:', fullGroup.name);
					}
				} catch (error) {
					console.error('[Management Dashboard] Error loading group', groupId, ':', error);
				}
			}

			availableGroups = groupsWithDashboard;
			console.log('[Management Dashboard] Final available groups:', availableGroups);
		} catch (error) {
			console.error('[Management Dashboard] Error loading groups:', error);
		} finally {
			loading = false;
		}
	};

	const openDashboard = (url) => {
		if (url) {
			window.open(url, '_blank');
		}
		showDropdown = false;
	};

	const toggleDropdown = () => {
		if (availableGroups.length === 1) {
			// Single group - open directly
			openDashboard(availableGroups[0].dashboardUrl);
		} else {
			// Multiple groups - show dropdown
			showDropdown = !showDropdown;
		}
	};

	// Close dropdown when clicking outside
	const handleClickOutside = (event) => {
		const button = event.target.closest('.management-dashboard-container');
		if (!button && showDropdown) {
			showDropdown = false;
		}
	};

	// Reload groups when user changes or managed_groups changes
	// Watch the user object directly to ensure reactivity
	$: {
		// This will run whenever $user changes at all
		if ($user) {
			console.log('[Management Dashboard] User changed, checking...', {
				role: $user.role,
				managed_groups: $user.managed_groups,
				has_managed_groups: !!$user.managed_groups
			});

			// Only load if user is a manager with managed groups
			if ($user.role === 'manager' && $user.managed_groups && $user.managed_groups.length > 0) {
				console.log('[Management Dashboard] User is manager with groups, loading...');
				loadGroups();
			}
		}
	}

	onMount(() => {
		console.log('[Management Dashboard] Component mounted, initial user:', $user);
		loadGroups();
		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

{#if $user?.role === 'manager' && availableGroups.length > 0 && !loading}
	<div class="management-dashboard-container relative">
		<button
			class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium text-sm transition-all shadow-sm hover:shadow-md"
			on:click={toggleDropdown}
			aria-label="Management Dashboard"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 16 16"
				fill="currentColor"
				class="size-4"
			>
				<path
					fill-rule="evenodd"
					d="M2 4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v1h10V4a1 1 0 0 0-1-1H4ZM3 7v5a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7H3Z"
					clip-rule="evenodd"
				/>
			</svg>
			<span>{$i18n.t('Management Dashboard')}</span>
		</button>

		{#if showDropdown && availableGroups.length > 1}
			<div
				class="absolute top-full right-0 mt-1 w-64 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
			>
				<div class="p-2">
					<div class="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 py-1">
						{$i18n.t('Select Group')}
					</div>
					{#each availableGroups as group}
						<button
							class="w-full text-left px-2 py-2 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
							on:click={() => openDashboard(group.dashboardUrl)}
						>
							{group.name}
						</button>
					{/each}
				</div>
			</div>
		{/if}
	</div>
{/if}
