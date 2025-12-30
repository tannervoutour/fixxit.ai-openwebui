<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import Spinner from '$lib/components/common/Spinner.svelte';
	import Logs from '$lib/components/icons/Logs.svelte';
	import LogsFilters from './LogsFilters.svelte';
	import { getLogs } from '$lib/apis/logs';

	export let availableGroups = [];

	// Logs viewing state
	let logs = [];
	let categories = [];
	let totalLogs = 0;
	let hasMore = false;
	let loading = false;

	// Filtering state
	let selectedCategory = '';
	let selectedBusinessImpact = '';
	let verifiedFilter: string = '';
	let equipmentFilter = '';
	let sortBy = 'created_at';
	let sortDesc = true;

	// Advanced filter options
	let dateRangeBefore = '';
	let dateRangeAfter = '';
	let selectedUser = '';
	let titleSearch = '';

	// Track previous filter values to detect changes
	let prevSelectedCategory = '';
	let prevVerifiedFilter = '';
	let prevEquipmentFilter = '';
	let prevSortBy = 'created_at';
	let prevSortDesc = true;
	let prevDateRangeAfter = '';
	let prevDateRangeBefore = '';
	let prevSelectedUser = '';
	let prevTitleSearch = '';

	const loadLogs = async () => {
		try {
			loading = true;

			const params = {
				limit: 20,
				offset: 0,
				sort_by: sortBy,
				sort_desc: sortDesc
			};

			// Basic filters
			if (selectedCategory) params.category = selectedCategory;
			if (selectedBusinessImpact) params.business_impact = selectedBusinessImpact;
			if (verifiedFilter !== '') params.verified = verifiedFilter === 'true';
			if (equipmentFilter) params.equipment = equipmentFilter;

			// Advanced filters based on sort type
			if (dateRangeAfter) params.date_after = dateRangeAfter;
			if (dateRangeBefore) params.date_before = dateRangeBefore;
			if (selectedUser) params.user_filter = selectedUser;
			if (titleSearch) params.title_search = titleSearch;

			const response = await getLogs(localStorage.token, params);

			if (response) {
				// Display debug information if available
				if (response.debug_info && response.debug_info.length > 0) {
					console.log('🔍 Backend Debug Info:');
					response.debug_info.forEach((info, index) => {
						console.log(`  ${index + 1}. ${info}`);
					});
				}

				logs = response.logs;
				totalLogs = response.total;
				hasMore = response.has_more;
				categories = response.categories;
			}
		} catch (error) {
			console.error('Error loading logs:', error);
			toast.error($i18n.t('Error loading logs'));
		} finally {
			loading = false;
		}
	};

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleString();
	};

	// Load logs on mount
	onMount(() => {
		loadLogs();
	});

	// Reload logs when any filter changes
	$: if (
		selectedCategory !== prevSelectedCategory ||
		verifiedFilter !== prevVerifiedFilter ||
		equipmentFilter !== prevEquipmentFilter ||
		sortBy !== prevSortBy ||
		sortDesc !== prevSortDesc ||
		dateRangeAfter !== prevDateRangeAfter ||
		dateRangeBefore !== prevDateRangeBefore ||
		selectedUser !== prevSelectedUser ||
		titleSearch !== prevTitleSearch
	) {
		prevSelectedCategory = selectedCategory;
		prevVerifiedFilter = verifiedFilter;
		prevEquipmentFilter = equipmentFilter;
		prevSortBy = sortBy;
		prevSortDesc = sortDesc;
		prevDateRangeAfter = dateRangeAfter;
		prevDateRangeBefore = dateRangeBefore;
		prevSelectedUser = selectedUser;
		prevTitleSearch = titleSearch;
		loadLogs();
	}
</script>

<div class="space-y-4">
	<!-- Filters Component -->
	<LogsFilters
		bind:selectedCategory
		bind:verifiedFilter
		bind:equipmentFilter
		bind:sortBy
		bind:dateRangeAfter
		bind:dateRangeBefore
		bind:selectedUser
		bind:titleSearch
		{categories}
	/>

	<!-- Logs List -->
	{#if loading}
		<div class="flex justify-center py-8">
			<Spinner className="size-6" />
		</div>
	{:else if logs.length === 0}
		<div class="text-center py-8 text-gray-500 dark:text-gray-400">
			<Logs className="size-12 mx-auto opacity-50 mb-4" strokeWidth="1.5" />
			<p class="text-lg font-medium mb-2">{$i18n.t('No logs found')}</p>
			<p class="text-sm">
				{availableGroups.length === 0
					? $i18n.t('No groups with database configuration found')
					: $i18n.t('No logs match your current filters')}
			</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each logs as log}
				<div
					class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 hover:shadow-md transition"
				>
					<div class="flex items-start justify-between mb-2">
						<h3 class="font-medium text-gray-900 dark:text-gray-100">{log.insight_title}</h3>
						<div class="flex items-center space-x-2">
							{#if log.verified}
								<span
									class="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded"
								>
									{$i18n.t('Verified')}
								</span>
							{/if}
							{#if log.problem_category}
								<span
									class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded"
								>
									{log.problem_category}
								</span>
							{/if}
						</div>
					</div>

					<p class="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">
						{log.insight_content}
					</p>

					<div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
						<span>{$i18n.t('By')} {log.user_name}</span>
						<span>{formatDate(log.created_at)}</span>
					</div>

					{#if log.source_group_name}
						<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
							{$i18n.t('Group')}: {log.source_group_name}
						</div>
					{/if}
				</div>
			{/each}
		</div>

		{#if hasMore}
			<div class="text-center pt-4">
				<button
					class="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
					on:click={loadLogs}
					disabled={loading}
				>
					{loading ? $i18n.t('Loading...') : $i18n.t('Load More')}
				</button>
			</div>
		{/if}
	{/if}
</div>
