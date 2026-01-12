<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { getGroupMembers, removeUserFromGroup, editUser, deleteUser } from '$lib/apis/managers';

	export let managedGroups = [];

	let selectedGroupId = '';
	let members = [];
	let loading = false;

	// Edit modal state
	let showEditModal = false;
	let editingUser = null;
	let editName = '';
	let editEmail = '';
	let editPassword = '';
	let saving = false;

	const loadMembers = async () => {
		if (!selectedGroupId) return;

		try {
			loading = true;
			const result = await getGroupMembers(localStorage.token, selectedGroupId);
			if (result) {
				members = result;
			}
		} catch (error) {
			console.error('Error loading members:', error);
			toast.error($i18n.t('Error loading group members'));
		} finally {
			loading = false;
		}
	};

	const handleRemoveFromGroup = async (userId: string, userName: string) => {
		if (!confirm($i18n.t('Remove {{name}} from this group?', { name: userName }))) {
			return;
		}

		try {
			const result = await removeUserFromGroup(localStorage.token, selectedGroupId, userId);
			if (result && result.success) {
				toast.success($i18n.t('User removed from group'));
				await loadMembers();
			}
		} catch (error) {
			console.error('Error removing user:', error);
			toast.error($i18n.t('Error removing user from group'));
		}
	};

	const handleDeleteUser = async (userId: string, userName: string) => {
		if (!confirm($i18n.t('Permanently delete user {{name}}? This cannot be undone.', { name: userName }))) {
			return;
		}

		try {
			const result = await deleteUser(localStorage.token, userId);
			if (result && result.success) {
				toast.success($i18n.t('User deleted successfully'));
				await loadMembers();
			}
		} catch (error) {
			console.error('Error deleting user:', error);
			toast.error($i18n.t('Error deleting user'));
		}
	};

	const openEditModal = (user) => {
		editingUser = user;
		editName = user.name;
		editEmail = user.email;
		editPassword = '';
		showEditModal = true;
	};

	const closeEditModal = () => {
		showEditModal = false;
		editingUser = null;
		editName = '';
		editEmail = '';
		editPassword = '';
	};

	const handleSaveEdit = async () => {
		if (!editingUser) return;

		const updates = {};
		if (editName !== editingUser.name) updates.name = editName;
		if (editEmail !== editingUser.email) updates.email = editEmail;
		if (editPassword) updates.password = editPassword;

		if (Object.keys(updates).length === 0) {
			toast.error($i18n.t('No changes to save'));
			return;
		}

		try {
			saving = true;
			const result = await editUser(localStorage.token, editingUser.id, updates);
			if (result && result.success) {
				toast.success($i18n.t('User updated successfully'));
				closeEditModal();
				await loadMembers();
			}
		} catch (error) {
			console.error('Error updating user:', error);
			toast.error($i18n.t('Error updating user'));
		} finally {
			saving = false;
		}
	};

	const formatDate = (timestamp: number) => {
		return new Date(timestamp * 1000).toLocaleString();
	};

	$: if (selectedGroupId) {
		loadMembers();
	}

	onMount(() => {
		if (managedGroups.length > 0) {
			selectedGroupId = managedGroups[0].id;
		}
	});
</script>

<div class="space-y-4">
	<!-- Group Selector -->
	<div>
		<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
			{$i18n.t('Select Group')}
		</label>
		<select
			bind:value={selectedGroupId}
			class="w-full max-w-md rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
		>
			{#each managedGroups as group}
				<option value={group.id}>{group.name} ({group.member_count} members)</option>
			{/each}
		</select>
	</div>

	<!-- Members List -->
	{#if loading}
		<div class="flex justify-center py-8">
			<Spinner className="size-6" />
		</div>
	{:else if members.length === 0}
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
					d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"
				/>
			</svg>
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
				{$i18n.t('No Members')}
			</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				{$i18n.t('This group has no members yet')}
			</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each members as member}
				<div
					class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
				>
					<div class="flex items-start justify-between">
						<div class="flex items-center gap-3 flex-1">
							<img
								src={member.profile_image_url}
								alt={member.name}
								class="size-12 rounded-full"
							/>
							<div>
								<h3 class="font-medium text-gray-900 dark:text-gray-100">{member.name}</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">{member.email}</p>
								<div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
									<span
										class="px-2 py-0.5 rounded {member.role === 'admin'
											? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
											: member.role === 'manager'
												? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
												: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}"
									>
										{member.role}
									</span>
									<span>{$i18n.t('Last active')}: {formatDate(member.last_active_at)}</span>
								</div>
							</div>
						</div>

						<div class="flex items-center gap-2 ml-4">
							<button
								on:click={() => openEditModal(member)}
								class="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
							>
								{$i18n.t('Edit')}
							</button>
							<button
								on:click={() => handleRemoveFromGroup(member.id, member.name)}
								class="px-3 py-1.5 text-sm text-orange-600 hover:text-orange-700 dark:text-orange-400 border border-orange-600 dark:border-orange-400 rounded hover:bg-orange-50 dark:hover:bg-orange-900/20 transition"
							>
								{$i18n.t('Remove')}
							</button>
							{#if member.role !== 'admin'}
								<button
									on:click={() => handleDeleteUser(member.id, member.name)}
									class="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 dark:text-red-400 border border-red-600 dark:border-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition"
								>
									{$i18n.t('Delete')}
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Edit Modal -->
{#if showEditModal && editingUser}
	<div
		class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
		on:click={closeEditModal}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
			on:click|stopPropagation
		>
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
				{$i18n.t('Edit User')}
			</h3>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Name')}
					</label>
					<input
						type="text"
						bind:value={editName}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Email')}
					</label>
					<input
						type="email"
						bind:value={editEmail}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('New Password')} <span class="text-xs text-gray-500">({$i18n.t('Optional')})</span>
					</label>
					<input
						type="password"
						bind:value={editPassword}
						placeholder={$i18n.t('Leave blank to keep current')}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					/>
				</div>
			</div>

			<div class="flex justify-end gap-3 mt-6">
				<button
					on:click={closeEditModal}
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
				>
					{$i18n.t('Cancel')}
				</button>
				<button
					on:click={handleSaveEdit}
					disabled={saving}
					class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition"
				>
					{saving ? $i18n.t('Saving...') : $i18n.t('Save Changes')}
				</button>
			</div>
		</div>
	</div>
{/if}
