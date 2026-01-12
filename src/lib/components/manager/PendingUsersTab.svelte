<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { getPendingUsers, approveUser, rejectUser } from '$lib/apis/managers';

	let pendingUsers = [];
	let loading = false;

	const loadPendingUsers = async () => {
		try {
			loading = true;
			const users = await getPendingUsers(localStorage.token);
			if (users) {
				pendingUsers = users;
			}
		} catch (error) {
			console.error('Error loading pending users:', error);
			toast.error($i18n.t('Error loading pending users'));
		} finally {
			loading = false;
		}
	};

	const handleApprove = async (userId: string, userName: string) => {
		try {
			const result = await approveUser(localStorage.token, userId);
			if (result && result.success) {
				toast.success($i18n.t('User {{name}} approved successfully', { name: userName }));
				await loadPendingUsers();
			}
		} catch (error) {
			console.error('Error approving user:', error);
			toast.error($i18n.t('Error approving user'));
		}
	};

	const handleReject = async (userId: string, userName: string) => {
		if (!confirm($i18n.t('Are you sure you want to reject and delete user {{name}}?', { name: userName }))) {
			return;
		}

		try {
			const result = await rejectUser(localStorage.token, userId);
			if (result && result.success) {
				toast.success($i18n.t('User {{name}} rejected and removed', { name: userName }));
				await loadPendingUsers();
			}
		} catch (error) {
			console.error('Error rejecting user:', error);
			toast.error($i18n.t('Error rejecting user'));
		}
	};

	const formatDate = (timestamp: number) => {
		return new Date(timestamp * 1000).toLocaleString();
	};

	onMount(() => {
		loadPendingUsers();
	});
</script>

<div class="space-y-4">
	{#if loading}
		<div class="flex justify-center py-8">
			<Spinner className="size-6" />
		</div>
	{:else if pendingUsers.length === 0}
		<div class="text-center py-12">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="size-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
				/>
			</svg>
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
				{$i18n.t('No Pending Users')}
			</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				{$i18n.t('All users have been approved or there are no new signups')}
			</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each pendingUsers as user}
				<div
					class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 hover:shadow-md transition"
				>
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center gap-3 mb-2">
								<img
									src={user.profile_image_url}
									alt={user.name}
									class="size-10 rounded-full"
								/>
								<div>
									<h3 class="font-medium text-gray-900 dark:text-gray-100">{user.name}</h3>
									<p class="text-sm text-gray-600 dark:text-gray-400">{user.email}</p>
								</div>
							</div>

							{#if user.pending_group_name}
								<div class="mt-2 flex items-center gap-2 text-sm">
									<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Invited to')}:</span>
									<span
										class="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded text-xs font-medium"
									>
										{user.pending_group_name}
									</span>
								</div>
							{/if}

							<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
								{$i18n.t('Signed up')}: {formatDate(user.created_at)}
							</div>
						</div>

						<div class="flex items-center gap-2 ml-4">
							<button
								on:click={() => handleApprove(user.id, user.name)}
								class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition"
							>
								{$i18n.t('Approve')}
							</button>
							<button
								on:click={() => handleReject(user.id, user.name)}
								class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition"
							>
								{$i18n.t('Reject')}
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
