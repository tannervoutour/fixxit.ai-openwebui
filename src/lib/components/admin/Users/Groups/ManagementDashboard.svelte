<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	import { updateGroupById, getGroupById } from '$lib/apis/groups';

	export let groupId: string = null;
	export let edit = false;

	let managementDashboardUrl = '';
	let loading = false;
	let loadedGroupId = null;

	const loadManagementDashboardConfig = async () => {
		if (!groupId) return;

		try {
			const group = await getGroupById(localStorage.token, groupId);

			if (group && group.data && group.data.management_dashboard_url) {
				managementDashboardUrl = group.data.management_dashboard_url;
			} else {
				managementDashboardUrl = '';
			}
		} catch (error) {
			console.error('Error loading management dashboard config:', error);
		}
	};

	$: if (groupId && groupId !== loadedGroupId) {
		loadManagementDashboardConfig();
		loadedGroupId = groupId;
	}

	const saveConfiguration = async () => {
		if (!groupId) {
			return false;
		}

		loading = true;

		try {
			// Get current group data
			const group = await getGroupById(localStorage.token, groupId);

			// Update the management_dashboard_url in the data object
			const updatedData = {
				...group.data,
				management_dashboard_url: managementDashboardUrl || null
			};

			// Update the group with new data
			await updateGroupById(localStorage.token, groupId, {
				name: group.name,
				description: group.description,
				data: updatedData
			});

			toast.success($i18n.t('Management dashboard configuration saved successfully'));

			return true;
		} catch (error) {
			console.error('Error saving management dashboard configuration:', error);
			toast.error($i18n.t('Error saving management dashboard configuration: ') + (error.message || 'Unknown error'));
			return false;
		} finally {
			loading = false;
		}
	};

	// Export the save function for parent component
	export { saveConfiguration as save };
</script>

<div class="flex flex-col space-y-4">
	<div class="text-sm text-gray-600 dark:text-gray-400">
		{$i18n.t('Configure the management dashboard URL for this group. Managers will be able to access this dashboard directly from the logs page.')}
	</div>

	<!-- Management Dashboard URL Input -->
	<div>
		<label for="management-dashboard-url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
			{$i18n.t('Management Dashboard URL')}
		</label>
		<input
			id="management-dashboard-url"
			bind:value={managementDashboardUrl}
			type="url"
			placeholder="https://cooperativekny.fixxit.ai"
			class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
		/>
		<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t('Enter the full URL including https://')}
		</div>
	</div>

	<!-- Help Text -->
	<div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
		<div class="text-sm text-blue-800 dark:text-blue-200">
			<div class="font-medium mb-2">{$i18n.t('Management Dashboard Setup:')}</div>
			<ul class="space-y-1 text-xs list-disc list-inside">
				<li>{$i18n.t('Managers will see a "Management Dashboard" button on the logs page')}</li>
				<li>{$i18n.t('Clicking the button will open the configured URL in a new tab')}</li>
				<li>{$i18n.t('Leave blank if no external management dashboard is needed')}</li>
				<li>{$i18n.t('Example: https://cooperativekny.fixxit.ai')}</li>
			</ul>
		</div>
	</div>
</div>
